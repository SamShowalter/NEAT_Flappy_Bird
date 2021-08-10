#!bin/bash
################################################################################
#
#             Script Title:   Training bash script for environment
#             Author:         Sam Showalter
#             Date:           2021-07-12
#
#################################################################################


#######################################################################
# Set variable names
#######################################################################

OUTPUT_DIR="models/"
ENV_NAME="Cameleon-Canniballs-Medium-12x12-v0"
NUM_EPOCHS=3900
NUM_EPISODES=0
NUM_TIMESTEPS=0
MODEL_NAME="DQN"
WRAPPERS="canniballs_one_hot,encoding_only"
CHECKPOINT_EPOCHS=20
CHECKPOINT_PATH="models/DQN_torch_Cameleon-Canniballs-Medium-12x12-v0_2021.08.05/checkpoint_003800/checkpoint-3800"
NUM_WORKERS=14
NUM_GPUS=1
FRAMEWORK="torch"
VERBOSE="true"
RAY_OBJ_STORE_MEM=3500000000
TUNE="false"

CONFIG="""{
'model':{'dim':12,
         'conv_filters':[[16,[4,4],1],
                         [32,[3,3],2],
                         [512,[6,6],1]]
        }
}"""

# Need to remove whitespaces
CONFIG="${CONFIG//[$'\t\r\n ']}"

#######################################################################
# Run the script for training
#######################################################################

# change to project root directory (in case invoked from other dir)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR/../"
clear

# Run the script
python -m cameleon.bin.train \
  --num-epochs=$NUM_EPOCHS \
  --num-episodes=$NUM_EPISODES \
  --num-timesteps=$NUM_TIMESTEPS \
  --env-name=$ENV_NAME \
  --model-name=$MODEL_NAME \
  --wrappers=$WRAPPERS \
  --num-workers=$NUM_WORKERS \
  --num-gpus=$NUM_GPUS \
  --checkpoint-epochs=$CHECKPOINT_EPOCHS \
  --outdir=$OUTPUT_DIR \
  --checkpoint-path=$CHECKPOINT_PATH \
  --framework=$FRAMEWORK \
  --tune=$TUNE \
  --ray-obj-store-mem=$RAY_OBJ_STORE_MEM \
  --config=$CONFIG \
  --verbose=$VERBOSE 
