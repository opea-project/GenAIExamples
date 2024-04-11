import "./results-list-item.scss";

import { arrayOf, shape, string } from "prop-types";
import { useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

import CustomPre from "./markdown/CustomPre";
import SourceGridItem from "./SourceGridItem";

const ResultsListItem = ({ dataItem, itemId }) => {
  const { question, answer, sources } = dataItem;

  const [sourcesOffset, setSourcesOffset] = useState(2);

  const onViewMoreClick = () => {
    setSourcesOffset(dataItem.sources.length);
  };

  return (
    <div id={itemId} className="results-card__results-list-item">
      <p className="question">{question}</p>
      <section className="answer">
        <Markdown
          remarkPlugins={[remarkGfm]}
          components={{
            pre: CustomPre,
          }}
        >
          {answer}
        </Markdown>
      </section>
      {sources.length > 0 && (
        <section className="sources-section">
          <p className="sources-section-title">Sources</p>
          <div className="sources-grid">
            {sources.slice(0, sourcesOffset).map((url, index) => (
              <SourceGridItem key={`${itemId}-${url}-${index}`} url={url} />
            ))}
            {sources.length > 3 && sourcesOffset < sources.length && (
              <div className="grid-item view-more-item" onClick={onViewMoreClick}>
                <p>View {sources.length - 2} more</p>
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
};

ResultsListItem.propTypes = {
  dataItem: shape({ question: string, answer: string, sources: arrayOf(string) }),
  itemId: string,
};

export default ResultsListItem;
