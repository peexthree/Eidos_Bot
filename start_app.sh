#!/bin/bash
alembic upgrade head
python3 bot.py > bot.log 2>&1 &
echo $! > bot.pid
