#!/bin/bash
mkdir -p ~/data/db
mongod --dbpath ~/data/db --fork --logpath ~/data/mongodb.log
