import io
import pandas as pd
from fastapi import APIRouter, Query, Body
from fastapi.responses import Response, JSONResponse

router = APIRouter()

COLS = ["adreca", "cp", "zt", "fecha", "x_lon", "y_lat"]


@router.post("/export")
def export(fmt: str = Query("csv"), payload: dict = Body(...)):
    rows = payload.get("rows", [])
    df = pd.DataFrame(rows, columns=COLS)
    if fmt == "json":
        return JSONResponse(df.to_dict(orient="records"))
    if fmt == "xlsx":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df.to_excel(w, index=False)
        return Response(
            content=buf.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=folletos.xlsx"})
    return Response(content=df.to_csv(index=False), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=folletos.csv"})
