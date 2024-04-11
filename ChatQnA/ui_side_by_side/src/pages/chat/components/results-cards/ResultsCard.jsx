import "./results-card.scss";

import LockIcon from "@mui/icons-material/Lock";
import { arrayOf, oneOf, shape, string } from "prop-types";
import { Fragment, useEffect } from "react";

import intelGaudiLogo from "../../../../assets/images/intel-gaudi-badge.png";
import intelXeonLogo from "../../../../assets/images/intel-xeon-badge.png";
import redisLogo from "../../../../assets/images/redis.svg";
import ResultsListItem from "./ResultsListItem";

const ResultsCard = ({ resultType, data }) => {
  const cardTitles = {
    "without-rag": "Stock Llama2 70b",
    "with-rag": "Stock Llama2 70b with RAG",
  };

  const resultCardListId = `${resultType}-list`;

  const scrollToChatBottom = () => {
    const resultCardList = document.getElementById(resultCardListId);
    resultCardList.scroll({ behavior: "instant", top: resultCardList.scrollHeight });
  };

  useEffect(() => {
    scrollToChatBottom();
  }, [data, resultCardListId]);

  return (
    <section className="results-card" id={resultType}>
      <div className="results-card-content">
        <header className={`results-card-header ${resultType}`}>
          <p className="results-card__title">{cardTitles[resultType]}</p>
        </header>
        <section className="results-card__results-list-wrapper" id={resultCardListId}>
          {data.length > 0 && (
            <div className="results-card__results-list">
              {data.map((dataItem, index) => (
                <Fragment key={`${index}-${resultType}`}>
                  <ResultsListItem dataItem={dataItem} itemId={`${index}-${resultType}`} />
                  {index !== data.length - 1 && <hr className="response-divider" />}
                </Fragment>
              ))}
            </div>
          )}
        </section>
      </div>
      <div className="results-card__logos">
        <img alt="Intel Xeon Logo" src={intelXeonLogo} />
        <img alt="Intel Gaudi Logo" src={intelGaudiLogo} />
        {resultType === "with-rag" && (
          <img alt="RedisDB logo" src={redisLogo} className="redis-logo" />
        )}
      </div>
      {resultType === "with-rag" && (
        <span className="with-rag-lock-icon">
          <LockIcon fontSize="small" />
        </span>
      )}
    </section>
  );
};

ResultsCard.propTypes = {
  resultType: oneOf(["without-rag", "with-rag"]),
  data: arrayOf(shape({ question: string, answer: string, sources: arrayOf(string) })),
};

export default ResultsCard;
