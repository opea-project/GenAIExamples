import { Modal, styled } from "@mui/material";

import styles from "./Modal.module.scss";

const StyledModalBox = styled("div")(({ theme }) => ({
  ...theme.customStyles.settingsModal,
}));

const ModalBox: React.FC<{
  children: React.ReactNode;
  open?: boolean;
  onClose?: () => void;
}> = ({ children, open = true, onClose }) => {
  let props: any = {};
  if (onClose) props.onClose = onClose;

  return (
    <Modal
      open={open}
      {...props}
      aria-labelledby="modal-modal-title"
      aria-describedby="modal-modal-description"
    >
      <StyledModalBox className={styles.modal}>{children}</StyledModalBox>
    </Modal>
  );
};

export default ModalBox;
