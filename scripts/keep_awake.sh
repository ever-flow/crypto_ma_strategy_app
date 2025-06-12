#!/bin/bash

# Streamlit 앱을 주기적으로 깨워서 슬립 상태를 방지
APP_URL=${APP_URL:-"https://your-streamlit-app-url"}

curl -s -o /dev/null "$APP_URL"
