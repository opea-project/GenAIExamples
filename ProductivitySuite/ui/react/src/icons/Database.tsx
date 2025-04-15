import { SvgIcon, useTheme } from "@mui/material";

interface DatabaseIconProps {
    className?: string;
}

const DatabaseIcon: React.FC<DatabaseIconProps> = ({className}) => {

    const theme = useTheme();
    const iconColor = theme.customStyles.icon?.main;

    return (
        <SvgIcon className={className}>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path fill={iconColor} d="M8 7.33333C9.66667 7.33333 11.0833 7.07222 12.25 6.55C13.4167 6.02778 14 5.4 14 4.66667C14 3.93333 13.4167 3.30556 12.25 2.78333C11.0833 2.26111 9.66667 2 8 2C6.33333 2 4.91667 2.26111 3.75 2.78333C2.58333 3.30556 2 3.93333 2 4.66667C2 5.4 2.58333 6.02778 3.75 6.55C4.91667 7.07222 6.33333 7.33333 8 7.33333ZM8 9C8.45555 9 9.02511 8.95267 9.70867 8.858C10.3922 8.76333 11.0504 8.61067 11.6833 8.4C12.3162 8.18933 12.8607 7.91444 13.3167 7.57533C13.7727 7.23622 14.0004 6.82222 14 6.33333V8C14 8.48889 13.7722 8.90289 13.3167 9.242C12.8611 9.58111 12.3167 9.856 11.6833 10.0667C11.05 10.2773 10.3918 10.4302 9.70867 10.5253C9.02556 10.6204 8.456 10.6676 8 10.6667C7.544 10.6658 6.97467 10.6184 6.292 10.5247C5.60933 10.4309 4.95089 10.2782 4.31667 10.0667C3.68244 9.85511 3.138 9.58022 2.68333 9.242C2.22867 8.90378 2.00089 8.48978 2 8V6.33333C2 6.82222 2.22778 7.23622 2.68333 7.57533C3.13889 7.91444 3.68333 8.18933 4.31667 8.4C4.95 8.61067 5.60844 8.76356 6.292 8.85867C6.97555 8.95378 7.54489 9.00089 8 9ZM8 12.3333C8.45555 12.3333 9.02511 12.286 9.70867 12.1913C10.3922 12.0967 11.0504 11.944 11.6833 11.7333C12.3162 11.5227 12.8607 11.2478 13.3167 10.9087C13.7727 10.5696 14.0004 10.1556 14 9.66667V11.3333C14 11.8222 13.7722 12.2362 13.3167 12.5753C12.8611 12.9144 12.3167 13.1893 11.6833 13.4C11.05 13.6107 10.3918 13.7636 9.70867 13.8587C9.02556 13.9538 8.456 14.0009 8 14C7.544 13.9991 6.97467 13.9518 6.292 13.858C5.60933 13.7642 4.95089 13.6116 4.31667 13.4C3.68244 13.1884 3.138 12.9136 2.68333 12.5753C2.22867 12.2371 2.00089 11.8231 2 11.3333V9.66667C2 10.1556 2.22778 10.5696 2.68333 10.9087C3.13889 11.2478 3.68333 11.5227 4.31667 11.7333C4.95 11.944 5.60844 12.0969 6.292 12.192C6.97555 12.2871 7.54489 12.3342 8 12.3333Z"/>
            </svg>   
        </SvgIcon>
    )
}

export default DatabaseIcon