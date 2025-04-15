import * as React from 'react';
import {
    Unstable_NumberInput as BaseNumberInput
} from '@mui/base/Unstable_NumberInput';
import { prepareForSlot } from '@mui/base/utils';
import { styled } from '@mui/material/styles';
import RemoveIcon from '@mui/icons-material/Remove';
import AddIcon from '@mui/icons-material/Add';
import { Typography } from '@mui/material';
import styles from './TokensInput.module.scss'

interface NumberInputProps {
    value?: number;
    handleChange: (value: number) => void;
    error:  boolean;
    readOnly?: boolean;
}

const StyledInput = styled('input')(({theme})=>({
  ...theme.customStyles.tokensInput,
}));

const StyledInputSlot = prepareForSlot(StyledInput);

const InputWrapper = styled(BaseNumberInput)(({ theme }) => ({}) );      

const TokensInput: React.FC<NumberInputProps> = ({value, handleChange, error, readOnly}) => {

    if(readOnly){
        return <Typography>{value}</Typography>;
    }

    return (
        <InputWrapper
            className={`${styles.numberInput} help`}
            aria-label="Quantity Input"
            min={1}
            max={4096}
            step={2}
            defaultValue={value}
            error={error}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleChange(parseInt(e.target.value, 10))}

            slots={{
                input: StyledInputSlot,
            }}

        />
    );

};

export default TokensInput;





