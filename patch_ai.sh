#!/bin/bash
sed -i 's/stream=True/stream=True, timeout=15.0/g' modules/services/ai_worker.py
