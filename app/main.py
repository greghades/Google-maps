from fastapi import FastAPI


app = FastAPI()


@app.get('/')
def read_root() -> dict[str, str]:
    return {"Message":"Hello World"}

@app.get("/get-services")
async def consult_api(service:str,location:str) -> dict[str, str]:

    return {"services":service,"location":location}





