set -e
set -x

# setup root
cd $PROTOCOL_DIR/
npm install &

# setup contracts
cd $PROTOCOL_DIR/
cd contracts/
npm install &

# setup eth contracts
cd $PROTOCOL_DIR/
cd eth-contracts/
npm install &

# no discovery provider setup needed
# 'pip install' is performed through Docker for development
# TODO: Revisit whether this is optimal after hot reloading for disc prov

# setup creator node
cd $PROTOCOL_DIR/
cd creator-node/
npm install &
npm install & #why does it not work without this?

# setup libs
cd $PROTOCOL_DIR/
cd libs/
npm install &

# setup identity service
cd $PROTOCOL_DIR/
cd identity-service/
npm install --dev &

wait
