import "./source-grid-item.scss";

import LinkIcon from "@mui/icons-material/Link";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import StorageIcon from "@mui/icons-material/Storage";
import { CircularProgress } from "@mui/material";
import { string } from "prop-types";
import { useState } from "react";

import ResultsService from "../../../../service/ResultsService";

const SourceGridItem = ({ url }) => {
  const [downloading, setDownloading] = useState(false);
  const [downloadNotification, setDownloadNotification] = useState({
    show: false,
    type: "", // 'success' | 'error'
    message: "",
  });

  const getSourceIcon = (url) => {
    if (url.startsWith("http")) {
      return <LinkIcon />;
    } else if (url.includes(".pdf")) {
      return <PictureAsPdfIcon />;
    } else {
      return <StorageIcon />;
    }
  };

  const getTitle = (url) => {
    if (url.startsWith("http")) {
      return url;
    } else {
      return url.split("/").slice(-1);
    }
  };

  const onSourceItemClick = (url) => {
    if (url !== null) {
      if (url.startsWith("http")) {
        window.open(url, "_blank");
      } else {
        setDownloading(true);
        ResultsService.downloadFile(url)
          .then((response) => response.blob())
          .then((blob) => {
            const blobURL = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.setAttribute("href", blobURL);
            const fileName = url.split("/").slice(-1);
            a.setAttribute("download", fileName);
            a.click();
            a.remove();
            setDownloadNotification({
              show: true,
              message: "Download successful",
              type: "success",
            });
          })
          .catch((error) => {
            console.error(error);
            setDownloadNotification({
              show: true,
              message: "Download failed",
              type: "error",
            });
          })
          .finally(() => {
            setTimeout(() => {
              setDownloading(false);
              setDownloadNotification((prevState) => ({
                ...prevState,
                show: false,
              }));
            }, 2000);
          });
      }
    }
  };

  return (
    <div
      className="grid-item"
      title={getTitle(url)}
      onClick={() => {
        if (!downloading) {
          onSourceItemClick(url);
        }
      }}
    >
      {url.includes(".pdf") && (
        <div
          className={`source-download-message ${downloadNotification.show && "visible"} ${downloadNotification.type}`}
        >
          {downloadNotification.message}
        </div>
      )}
      <div
        className={`source-grid-item ${url !== null && !downloading && "downloadable-source-item"} ${downloading && "downloading"}`}
      >
        <span className="source-grid-item__icon">
          {downloading ? <CircularProgress size={"1.5rem"} /> : getSourceIcon(url)}
        </span>
        <p className="source-title">{getTitle(url)}</p>
      </div>
    </div>
  );
};

SourceGridItem.propTypes = {
  url: string,
};

export default SourceGridItem;
