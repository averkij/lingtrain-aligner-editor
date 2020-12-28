USE_BATCHSIZE=${VAR_BATCHSIZE:-'50'}
USE_WINDOW=${VAR_WINDOW:-'40'}
USE_MAX_BATCHES=${VAR_MAX_BATCHES:-'4'}
USE_PROCESSORS_COUNT=${VAR_PROCESSORS_COUNT:-'2'}

sed -i "s/VAR_BATCHSIZE/$USE_BATCHSIZE/g" /app/config.py
sed -i "s/VAR_WINDOW/$USE_WINDOW/g" /app/config.py
sed -i "s/VAR_MAX_BATCHES/$USE_MAX_BATCHES/g" /app/config.py
sed -i "s/VAR_PROCESSORS_COUNT/$USE_PROCESSORS_COUNT/g" /app/config.py
