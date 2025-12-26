import aiohttp
import asyncio

from models import init_orm, close_orm, DbSession, SwapiPeople

async def get_people_data( link, httpsession ):
    print(f"processing {link}")
    responce = await httpsession.get( f"{link}" )
    json_data = await responce.json()
    
    return json_data

async def get_person( link, httpsession ):
    responce = await httpsession.get( f"{link}" )
    json_data = await responce.json()
    out = json_data['result']['properties']
    out['homeworld_name'] = await get_homeworld_name( out['homeworld'], httpsession ) 

    return out


async def get_homeworld_name( link, httpsession ):
    responce = await httpsession.get( f"{link}" )
    json_data = await responce.json()

    return json_data['result']['properties']['name']

async def insert_results( people_list: list[dict] ):
    async with DbSession() as dbsession:
        orm_objects = []
        for people in people_list:
            orm_obj = SwapiPeople( 
                name = people['name'], 
                gender = people['gender'],
                birth_year = people['birth_year'],
                homeworld = people['homeworld_name'] ,
                mass = people['mass'],
                skin_color = people['skin_color'],
                hair_color = people['hair_color'],
                eye_color = people['eye_color'],
            )
            orm_objects.append( orm_obj )
        dbsession.add_all( orm_objects )
        await dbsession.commit()


async def main():
    await init_orm()
    
    # Решение: пробежаться циклом по постраничному списку персонажей, добавить их в базу.
    next_page = 'https://www.swapi.tech/api/people/' # Стартовая страница
    while True:
        # Пришлось запускать сессию каждую итерацию цикла, иначе не приходят данные
        # Возможно ограничения API
        async with aiohttp.ClientSession() as httpsession: 
            # Запрос страницы персонажей и ссылко на них
            people_data = await get_people_data( next_page, httpsession ) 
            next_page = people_data['next']

            # Запросы по ссылкам на персонажей
            list_results = [ get_person( person['url'], httpsession ) for person in people_data['results'] ]
            results = await asyncio.gather( *list_results ) 
                       
            await insert_results( results )

        if next_page == None: # Выход из цикла когда отсутствует ссылка на следующую страницу 
            break


    await close_orm()


asyncio.run( main() )