from functools import wraps
from discord.ext import commands
from database.manager import db_manager
import discord

def get_server_role(server_id):
    with db_manager.get_cursor() as cursor:
        cursor.execute('SELECT role_name FROM server_roles WHERE server_id = ?', (server_id,))
        result = cursor.fetchone()
    return result['role_name'] if result else '@everyone'

def has_required_role():
    async def predicate(interaction):
        required_role = get_server_role(interaction.guild_id)
        return any(role.name == required_role for role in interaction.user.roles)
    return commands.check(predicate)

def has_role_or_everyone():
    async def predicate(ctx):
        role_name = get_server_role(ctx.guild.id)
        return discord.utils.get(ctx.author.roles, name=role_name) is not None or discord.utils.get(ctx.author.roles, name='@everyone') is not None
    return commands.check(predicate)

def error_handler():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                print(f"Error in {func.__name__}: {str(e)}")
                if isinstance(args[0], commands.Context):
                    await args[0].send(f"An error occurred: {str(e)}")
        return wrapper
    return decorator