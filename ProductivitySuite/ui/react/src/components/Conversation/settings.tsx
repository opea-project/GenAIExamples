import { NumberInput, Slider, Text, Title } from "@mantine/core"
import { useAppDispatch, useAppSelector } from "../../redux/store"
import { conversationSelector, setTemperature, setToken } from "../../redux/Conversation/ConversationSlice"



function Settings() {
    const { token,maxTemperature, minTemperature, maxToken, minToken, temperature} = useAppSelector(conversationSelector)
    const dispatch = useAppDispatch();
    
    const onTemperatureChange = (value: number) => {
        dispatch(setTemperature(value))
    }
    const onTokenChange = (value: number | string) => {
        dispatch(setToken(Number(value)))
    }

    return (
        <>
            <div>
                <Title order={4}>Settings</Title>
            </div>
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