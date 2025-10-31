#!/usr/bin/env python3
"""
Komorebi CLI - Management commands for the Komorebi API
"""
import click
from scripts.seed_roles import create_role, list_roles


@click.group()
def cli():
    """Komorebi management CLI"""
    pass


@cli.command(name='create-role')
@click.option('--role', '-r', required=True, help='Name of the role to create')
def create_role_cmd(role):
    """Create a new role"""
    create_role(role)


@cli.command(name='list-roles')
def list_roles_cmd():
    """List all existing roles"""
    list_roles()


if __name__ == '__main__':
    cli()
