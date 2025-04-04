from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import aiomysql
from typing import List

app = FastAPI()

class Item(BaseModel):
    username: str
    email: str
    id:int=None

async def get_db():
    pool = await aiomysql.create_pool(
        host="localhost",
        user="root",
        password="121234",
        db="test"
    )
    async with pool.acquire() as conn:
        yield conn
    pool.close()
    await pool.wait_closed()
@app.get("/items/", response_model=List[Item])
async def get_items(db=Depends(get_db)):
    async with db.cursor() as cur:
        await cur.execute("SELECT  username, email,id FROM user")
        rows = await cur.fetchall()
    return [
    {
        "id": int(row[2]) if isinstance(row[2], (int, str)) and str(row[2]).isdigit() else None,  # Ensure id is an integer
        "username": str(row[0]),  # Ensure username is a string
        "email": str(row[1])  # Ensure email is a string
    }
    for row in rows
]


    
@app.post("/items/", response_model=Item)
async def create_item(item: Item, db: aiomysql.Connection = Depends(get_db)):
    async with db.cursor() as cur:
        await cur.execute(
            "INSERT INTO user (username, email ,id) VALUES (%s, %s,%s)",
            (item.username, item.email,item.id)
        )
        item_id = cur.lastrowid
        await db.commit()
    return {"id": item_id, **item.model_dump()}

@app.get("/items/{item_id}",response_model=Item)
async def read_item(item_id:int,db=Depends(get_db)):
    async with db.cursor() as cur:
        await cur.execute("SELECT * FROM user WHERE id =%s",(item_id,))
        row=await cur.fetchone()
        print(row)
    if not row:
        raise HTTPException(status_code=404,details="item not found")
    item=Item(id=row[2],username=row[0],email=row[1])
    return item

@app.put("/items/{item_id}",response_model=Item)
async def update_item(item_id:int, item:Item,db=Depends(get_db)):
    async with  db.cursor() as cur:
        await cur.execute(
            "UPDATE user SET username=%s,email=%s WHERE id = %s",
            (item.username,item.email,item_id)
        )
        await db.commit()
    return await read_item (item_id,db=db)
    
@app.delete("/items/{item_id}")
async def delete_item(item_id:int,db=Depends(get_db)):
    async with db.cursor() as cur:
        await cur.execute("DELETE FROM user WHERE id=%s",(item_id,))
        await db.commit()
        return {"message":"item deleted sucessfully"}