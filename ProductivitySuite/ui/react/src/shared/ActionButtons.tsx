import { Button, styled } from "@mui/material";

const TextOnlyStyle = styled(Button)(({ theme }) => ({
  ...theme.customStyles.actionButtons.text,
}));

const DeleteStyle = styled(Button)(({ theme }) => ({
  ...theme.customStyles.actionButtons.delete,
}));

const SolidStyle = styled(Button)(({ theme }) => ({
  ...theme.customStyles.actionButtons.solid,
}));

const OutlineStyle = styled(Button)(({ theme }) => ({
  ...theme.customStyles.actionButtons.outline,
}));

type ButtonProps = {
  onClick: (value: boolean) => void;
  children: React.ReactNode | React.ReactNode[];
  disabled?: boolean;
  className?: string;
};

const TextButton: React.FC<ButtonProps> = ({
  onClick,
  children,
  disabled = false,
  className,
}) => {
  return (
    <TextOnlyStyle
      disabled={disabled}
      onClick={() => onClick(true)}
      className={className}
    >
      {children}
    </TextOnlyStyle>
  );
};

const DeleteButton: React.FC<ButtonProps> = ({
  onClick,
  children,
  disabled = false,
  className,
}) => {
  return (
    <DeleteStyle
      disabled={disabled}
      onClick={() => onClick(true)}
      className={className}
    >
      {children}
    </DeleteStyle>
  );
};

const SolidButton: React.FC<ButtonProps> = ({
  onClick,
  children,
  disabled = false,
  className,
}) => {
  return (
    <SolidStyle
      disabled={disabled}
      onClick={() => onClick(true)}
      className={className}
    >
      {children}
    </SolidStyle>
  );
};

const OutlineButton: React.FC<ButtonProps> = ({
  onClick,
  children,
  disabled = false,
  className,
}) => {
  return (
    <OutlineStyle
      disabled={disabled}
      onClick={() => onClick(true)}
      className={className}
    >
      {children}
    </OutlineStyle>
  );
};

export { TextButton, DeleteButton, SolidButton, OutlineButton };
