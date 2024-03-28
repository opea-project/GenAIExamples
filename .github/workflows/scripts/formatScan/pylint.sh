#!/bin/bash

source /GenAIExamples/.github/workflows/scripts/change_color
cd /GenAIExamples
pip install -U pip
$BOLD_YELLOW && echo "---------------- git submodule update --init --recursive -------------" && $RESET
git config --global --add safe.directory "*"
git submodule update --init --recursive

export PYTHONPATH=$(pwd)
pip install langchain fastapi
pip list

cd /GenAIExamples
log_dir=/GenAIExamples/.github/workflows/scripts/formatScan

echo "[DEBUG] list pipdeptree..."
pip install pipdeptree
pipdeptree

python -m pylint -f json --disable=R,C,W,E1129 \
    --enable=line-too-long \
    --max-line-length=120 \
    --extension-pkg-whitelist=numpy,nltk \
    --ignored-classes=TensorProto,NodeProto \
    --ignored-modules=tensorflow,torch,torch.quantization,torch.tensor,torchvision,mxnet,onnx,onnxruntime,neural_compressor,neural_compressor.benchmark,intel_extension_for_transformers.neural_engine_py,cv2,PIL.Image \
    /GenAIExamples >${log_dir}/pylint.json
exit_code1=$?

$BOLD_YELLOW && echo " -----------------  Current log file output start --------------------------" && $RESET
cat ${log_dir}/pylint.json
$BOLD_YELLOW && echo " -----------------  Current log file output end --------------------------" && $RESET

if [ ${exit_code1} -ne 0 ] || [ ${exit_code2} -ne 0 ]; then
    $BOLD_RED && echo "Error!! Please Click on the artifact button to download and view Pylint error details." && $RESET
    exit 1
fi
$BOLD_PURPLE && echo "Congratulations, Pylint check passed!" && $LIGHT_PURPLE && echo " You can click on the artifact button to see the log details." && $RESET
exit 0
