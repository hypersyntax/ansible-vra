#!/bin/bash

ansible-playbook blueprint_pipeline.yml --extra-vars "blueprint_name=Linux retries=30"