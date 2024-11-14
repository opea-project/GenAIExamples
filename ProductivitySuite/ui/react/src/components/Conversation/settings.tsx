import { NumberInput, Select, Slider, Text, Title } from "@mantine/core"
import { useAppDispatch, useAppSelector } from "../../redux/store"
import { conversationSelector, setTemperature, setToken, setModel, setMinToken, setMaxToken, setModels} from "../../redux/Conversation/ConversationSlice"
import { useEffect } from "react";


function Settings() {
    const { token, maxTemperature, minTemperature, maxToken, minToken, temperature, models, model } = useAppSelector(conversationSelector)
    const dispatch = useAppDispatch();

    const modelOptions = models.map(model => ({
        value: model.model_name,
        label: model.displayName,
        minToken: model.minToken,
        maxToken: model.maxToken,
    }));

    const onModelChange = (value: string | null) => {
        if (value) {
            const selectedModel = models.find(m => m.model_name === value);
            if (selectedModel) {
                dispatch(setModel(value));
                dispatch(setTemperature(0.4)); // Assuming you want to reset to a default value
                dispatch(setToken(selectedModel.minToken));
                dispatch(setMinToken(selectedModel.minToken));
                dispatch(setMaxToken(selectedModel.maxToken));
                // You might also want to update the min and max token values in the redux state here
            }
        }
    };
    const onTemperatureChange = (value: number) => {
        dispatch(setTemperature(value))
    }
    const onTokenChange = (value: number | string) => {
        dispatch(setToken(Number(value)))
    }

    const callFunctions = async () => {
        try {
            const response = await fetch('/model_configs.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const model_configs = await response.json();
            // Check if the array is empty
            if (model_configs.length === 0) {
                throw new Error('The model_configs.json file contains an empty array.');
            }
            // Validate that each object contains the required fields with non-empty values
            const requiredFields = ['model_name', 'displayName', 'endpoint', 'minToken', 'maxToken'];
            for (const config of model_configs) {
                for (const field of requiredFields) {
                    if (!(field in config) || config[field] === '') {
                        throw new Error(`One or more configurations are missing the required field '${field}' or the field is empty.`);
                    }
                }
            }
            // After validation, update the state with the new configs
            dispatch(setModels(model_configs));
            dispatch(setMinToken(model_configs[0].minToken));
            dispatch(setMaxToken(model_configs[0].maxToken));
            dispatch(setModel(model_configs[0].model_name));
        } catch (error) {
            console.warn('model_configs.json not found, using default configuration.', error);
            // If the fetch fails, the state will remain with the default values
        }
    }
    
    useEffect(() => {
        callFunctions()
    }, [])

    return (
        <>
        
            <div>
                <Title order={4}>Settings</Title>
            </div>
            {models.length > 0 && (
                <div>
                    <Select
                        label="Model"
                        placeholder="Pick a model"
                        value={model}
                        onChange={onModelChange}
                        data={modelOptions}
                    />
                </div>
            )}
            <div>
                <Text>Temperature</Text>
                <Slider
                    value={temperature}
                    min={minTemperature}
                    max={maxTemperature}
                    step={0.1}
                    onChange={onTemperatureChange}
                />
            </div>
            <div>
                <Text>Token ({`${minToken} - ${maxToken}`})</Text>
                <NumberInput
                    value={token}
                    min={minToken}
                    max={maxToken}
                    step={100}
                    onChange={onTokenChange}
                />
            </div>
        </>
        
    )
}

export default Settings
