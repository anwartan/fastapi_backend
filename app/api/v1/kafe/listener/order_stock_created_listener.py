import asyncio

async def listener():
    await asyncio.sleep(5)
    print("Order stock created listener triggered")