from functools import wraps
import logging
from typing import Dict, Any

import asyncpg

import libs.env as env


class ProductionDatabase:
    def __init__(self):
        self.pool = None

    async def setup(self):
        self.pool = await asyncpg.create_pool(f"postgresql://{env.POSTGRESQL_USER}:{env.POSTGRESQL_PASSWORD}@{env.POSTGRESQL_HOST_NAME}:{env.POSTGRESQL_PORT}/{env.POSTGRESQL_DATABASE_NAME}")

        async with self.pool.acquire() as conn:
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS valo_name_data (guild_id bigint NOT NULL, user_id bigint NOT NULL, valo_name TEXT NOT NULL, PRIMARY KEY (guild_id, user_id)")
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS guild_ch_data (guild_id bigint NOT NULL PRIMARY KEY, ch_first_id bigint NOT NULL, ch_second_id bigint NOT NULL)")

        return self.pool

    def check_connection(func):
        @wraps(func)
        async def inner(self, *args, **kwargs):
            self.pool = self.pool or await self.setup()
            return await func(self, *args, **kwargs)

        return inner

    @check_connection
    async def execute(self, sql):
        async with self.pool.acquire() as con:
            await con.execute(sql)

    @check_connection
    async def fetch(self, sql):
        async with self.pool.acquire() as con:
            data = await con.fetch(sql)
        return data

    @check_connection
    async def get_name_from_user(self, user_id: int, guild_id: int) -> str | None:
        """Get Valorant name from user ID and guild ID."""
        async with self.pool.acquire() as con:
            data = await con.fetch('SELECT valo_name FROM valo_name_data WHERE user_id=$1 AND guild_id=$2', user_id, guild_id)
            if data:
                return data[0].get('valo_name')
            else:
                return None

    @check_connection
    async def get_all_names_in_guild(self, guild_id: int) -> dict[Any, Any]:
        """Get all Valorant names in a guild."""
        async with self.pool.acquire() as con:
            data = await con.fetch('SELECT user_id, valo_name FROM valo_name_data WHERE guild_id=$1', guild_id)
            res_data = {}
            for record in data:
                res_data[record['user_id']] = record['valo_name']
            return res_data

    @check_connection
    async def set_name_for_user(self, user_id: int, guild_id: int, valo_name: str) -> None:
        """Set Valorant name for user ID and guild ID."""
        async with self.pool.acquire() as con:
            await con.execute('INSERT INTO valo_name_data (guild_id, user_id, valo_name) VALUES ($1, $2, $3) ON CONFLICT (guild_id, user_id) DO UPDATE SET valo_name = EXCLUDED.valo_name', guild_id, user_id, valo_name)

    @check_connection
    async def delete_name_for_user(self, user_id: int, guild_id: int) -> None:
        """Delete Valorant name for user ID and guild ID."""
        async with self.pool.acquire() as con:
            await con.execute('DELETE FROM valo_name_data WHERE user_id=$1 AND guild_id=$2', user_id, guild_id)

    @check_connection
    async def get_guild_channel_data(self, guild_id: int) -> tuple[int, int] | tuple[None, None]:
        """Get guild channel data."""
        async with self.pool.acquire() as con:
            data = await con.fetch('SELECT ch_first_id, ch_second_id FROM guild_ch_data WHERE guild_id=$1', guild_id)
            if data:
                return data[0].get('ch_first_id'), data[0].get('ch_second_id')
            else:
                return None, None

    @check_connection
    async def set_guild_channel_data(self, guild_id: int, ch_first_id: int, ch_second_id: int) -> None:
        """Set guild channel data."""
        async with self.pool.acquire() as con:
            await con.execute('INSERT INTO guild_ch_data (guild_id, ch_first_id, ch_second_id) VALUES ($1, $2, $3) ON CONFLICT (guild_id) DO UPDATE SET ch_first_id = EXCLUDED.ch_first_id, ch_second_id = EXCLUDED.ch_second_id', guild_id, ch_first_id, ch_second_id)


    @check_connection
    async def delete_guild_channel_data(self, guild_id: int) -> None:
        """Delete guild channel data."""
        async with self.pool.acquire() as con:
            await con.execute('DELETE FROM guild_ch_data WHERE guild_id=$1', guild_id)


class DebugDatabase(ProductionDatabase):
    async def setup(self):
        self.pool = None

    async def execute(self, sql):
        logging.info(f"executing sql: {sql}")

    async def fetch(self, sql):
        logging.info(f"fetching sql: {sql}")

    async def get_name_from_user(self, user_id: int, guild_id: int) -> str | None:
        logging.info(f"getting name for user_id: {user_id}, guild_id: {guild_id}")
        return "Debug_Valorant_Name"

    async def set_name_for_user(self, user_id: int, guild_id: int, valo_name: str) -> None:
        logging.info(f"setting name for user_id: {user_id}, guild_id: {guild_id}, valo_name: {valo_name}")

    async def delete_name_for_user(self, user_id: int, guild_id: int) -> None:
        logging.info(f"deleting name for user_id: {user_id}, guild_id: {guild_id}")

    async def get_all_names_in_guild(self, guild_id: int) -> list[tuple[int, str]]:
        logging.info(f"getting all names in guild_id: {guild_id}")
        return [(111111111111111111, "Debug_Name_1"), (222222222222222222, "Debug_Name_2")]

    async def get_guild_channel_data(self, guild_id: int) -> tuple[int, int] | tuple[None, None]:
        logging.info(f"getting guild channel data for guild_id: {guild_id}")
        return 123456789012345678, 987654321098765432

    async def set_guild_channel_data(self, guild_id: int, ch_first_id: int, ch_second_id: int) -> None:
        logging.info(f"setting guild channel data for guild_id: {guild_id}, ch_first_id: {ch_first_id}, ch_second_id: {ch_second_id}")

    async def delete_guild_channel_data(self, guild_id: int) -> None:
        logging.info(f"deleting guild channel data for guild_id: {guild_id}")


if env.DEBUG == 1:
    Database = DebugDatabase
else:
    Database = ProductionDatabase
