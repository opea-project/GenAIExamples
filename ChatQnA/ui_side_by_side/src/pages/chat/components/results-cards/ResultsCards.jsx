import "./results-cards.scss";

import { arrayOf, exact, shape, string } from "prop-types";

import ResultsCard from "./ResultsCard";

const ResultsCards = ({ data }) => {
  return (
    <div className="results-cards">
      <ResultsCard resultType="without-rag" data={data.withoutRAG} />
      <ResultsCard resultType="with-rag" data={data.withRAG} />
    </div>
  );
};

ResultsCards.propTypes = {
  data: exact({
    withoutRAG: arrayOf(shape({ question: string, answer: string, sources: arrayOf(string) })),
    withRAG: arrayOf(shape({ question: string, answer: string, sources: arrayOf(string) })),
  }),
};

export default ResultsCards;
