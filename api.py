from fastapi import FastAPI, File, UploadFile

app = FastAPI()

log_files = "/Volumes/GoogleDrive/Shared drives/NY Tech Drive/computer_logs"


@app.get("/")
async def main():
    print("Testing!")
    return {"Name": "testing"}


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    file_name = file.filename
    print(f"Received File: {file_name}")
    contents = await file.read()
    with open(f"{log_files}/{file_name}", "w") as the_file:
        the_file.write(contents.decode())
    return {"File Received"}
