#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
from dotenv import load_dotenv


load_dotenv("../../.env")

class DefaultConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("APP_ID", "")
    APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
