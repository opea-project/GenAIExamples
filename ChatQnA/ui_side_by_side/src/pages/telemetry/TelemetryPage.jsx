import "./telemetry-page.scss";

import LockIcon from "@mui/icons-material/Lock";
import { useEffect, useState } from "react";

import intelGaudiLogo from "../../assets/images/intel-gaudi-badge.png";
import intelXeonLogo from "../../assets/images/intel-xeon-badge.png";

const TelemetryPage = () => {
  const [metrics, setMetrics] = useState({
    latency_without_rag: localStorage.getItem("latency_without_rag"),
    llm_token_latency_without_rag: localStorage.getItem("llm_token_latency_without_rag"),
    latency_with_rag: localStorage.getItem("latency_with_rag"),
    llm_token_latency_with_rag: localStorage.getItem("llm_token_latency_with_rag"),
    retriver_latency: localStorage.getItem("retriver_latency"),
    input_token_size_without_rag: localStorage.getItem("input_token_size_without_rag"),
    output_token_size_without_rag: localStorage.getItem("output_token_size_without_rag"),
    first_token_latency_without_rag: localStorage.getItem("first_token_latency_without_rag"),
    input_token_size_with_rag: localStorage.getItem("input_token_size_with_rag"),
    output_token_size_with_rag: localStorage.getItem("output_token_size_with_rag"),
    first_token_latency_with_rag: localStorage.getItem("first_token_latency_with_rag"),
  });

  const onStorageUpdate = () => {
    const latency_without_rag = localStorage.getItem("latency_without_rag");
    const llm_token_latency_without_rag = localStorage.getItem("llm_token_latency_without_rag");
    const latency_with_rag = localStorage.getItem("latency_with_rag");
    const llm_token_latency_with_rag = localStorage.getItem("llm_token_latency_with_rag");
    const retriver_latency = localStorage.getItem("retriver_latency");
    const input_token_size_without_rag = localStorage.getItem("input_token_size_without_rag");
    const output_token_size_without_rag = localStorage.getItem("output_token_size_without_rag");
    const first_token_latency_without_rag = localStorage.getItem("first_token_latency_without_rag");
    const input_token_size_with_rag = localStorage.getItem("input_token_size_with_rag");
    const output_token_size_with_rag = localStorage.getItem("output_token_size_with_rag");
    const first_token_latency_with_rag = localStorage.getItem("first_token_latency_with_rag");

    const newMetrics = {
      latency_without_rag,
      llm_token_latency_without_rag,
      latency_with_rag,
      llm_token_latency_with_rag,
      retriver_latency,
      input_token_size_without_rag,
      output_token_size_without_rag,
      first_token_latency_without_rag,
      input_token_size_with_rag,
      output_token_size_with_rag,
      first_token_latency_with_rag,
    };

    setMetrics(newMetrics);
  };

  useEffect(() => {
    onStorageUpdate();
    window.addEventListener("storage", onStorageUpdate);
    return () => {
      window.removeEventListener("storage", onStorageUpdate);
    };
  }, []);

  const convertValue = (value, isTokenSize = false) => {
    const emptyValues = [null, "null", undefined, "NaN", "Infinity", "undefined"];
    if (isTokenSize) {
      return emptyValues.includes(value) ? "N/A" : value;
    } else {
      if (emptyValues.includes(value)) {
        return "N/A";
      } else {
        const numValue = +parseFloat(value);
        if (numValue >= 1000) {
          return `${(numValue / 1000).toFixed(1)}\xa0sec`;
        } else if (numValue < 1) {
          return `${numValue.toFixed(3)}\xa0ms`;
        } else {
          return `${numValue.toFixed(1)}\xa0ms`;
        }
      }
    }
  };

  return (
    <main className="telemetry-page">
      <section className="telemetry-graph">
        <section className="client-section">
          <h2 className="section-title">Client</h2>
          <div className="client-box"></div>
        </section>
        <section className="llm-section">
          <h2 className="section-title">LLM</h2>
          <div className="llm-box">
            <img alt="Intel Gaudi Logo" src={intelGaudiLogo} />
          </div>
        </section>
        <div className="flow-box">
          <div className="inference-flow without-rag">
            <div className="latency-metrics">
              <div className="latency-metric-label">
                <label>
                  <span>Latency</span>
                  <span>Without&nbsp;RAG</span>
                </label>
                <span className="divider"></span>
                <span className="latency-metric-value">
                  {convertValue(metrics.latency_without_rag)}
                </span>
              </div>
            </div>
            <div className="io-flow">
              <div className="arrow white right">
                <p className="input-token-size-label">
                  Input Token Size: {convertValue(metrics.input_token_size_without_rag, true)}
                </p>
                <div className="arrow-head"></div>
                <div className="arrow-body"></div>
              </div>
              <div className="arrow blue">
                <div className="arrow-head"></div>
                <div className="arrow-body"></div>
                <p className="output-token-size-label">
                  Output Token Size: {convertValue(metrics.output_token_size_without_rag, true)}
                </p>
              </div>
            </div>
            <div className="token-metrics">
              <div className="latency-metric-label">
                <label>
                  <span>
                    First&nbsp;Token
                    <br />
                    Latency
                  </span>
                </label>
                <span className="divider"></span>
                <span className="latency-metric-value">
                  {convertValue(metrics.first_token_latency_without_rag)}
                </span>
              </div>
              <div className="latency-metric-label">
                <label>
                  <span>
                    LLM&nbsp;Token
                    <br />
                    Latency
                    <br />
                    Without&nbsp;RAG
                  </span>
                </label>
                <span className="divider"></span>
                <span className="latency-metric-value">
                  {convertValue(metrics.llm_token_latency_without_rag)}
                </span>
              </div>
            </div>
          </div>
          <div className="inference-flow with-rag">
            <div className="latency-metrics">
              <div className="latency-metric-label">
                <label>
                  <span>Latency</span>
                  <span>With&nbsp;RAG</span>
                </label>
                <span className="divider"></span>
                <span className="latency-metric-value">
                  {convertValue(metrics.latency_with_rag)}
                </span>
              </div>
            </div>
            <div className="io-flow">
              <div className="vector-database-flow">
                <div className="arrow white right">
                  <p className="input-token-size-label">
                    Input Token Size: {convertValue(metrics.input_token_size_with_rag, true)}
                  </p>
                  <div className="arrow-head"></div>
                  <div className="arrow-body"></div>
                </div>
                <div className="vector-database-box">
                  <p>
                    Vector <br />
                    Database
                  </p>
                  <span className="with-rag-lock-icon">
                    <LockIcon fontSize="small" />
                  </span>
                  <img alt="Intel Xeon Logo" src={intelXeonLogo} className="intel-xeon-logo" />
                </div>
                <div className="arrow blue">
                  <div className="arrow-head"></div>
                  <div className="arrow-body"></div>
                  <p className="output-token-size-label">
                    Output Token Size: {convertValue(metrics.output_token_size_with_rag, true)}
                  </p>
                </div>
              </div>
            </div>
            <div className="token-metrics">
              <div className="latency-metric-label">
                <label>
                  <span>
                    First&nbsp;Token
                    <br />
                    Latency
                  </span>
                </label>
                <span className="divider"></span>
                <span className="latency-metric-value">
                  {convertValue(metrics.first_token_latency_with_rag)}
                </span>
              </div>
              <div className="latency-metric-label">
                <label>
                  <span>
                    LLM&nbsp;Token
                    <br />
                    Latency
                    <br />
                    With&nbsp;RAG
                  </span>
                </label>
                <span className="divider"></span>
                <span className="latency-metric-value">
                  {convertValue(metrics.llm_token_latency_with_rag)}
                </span>
              </div>
            </div>
            <div className="other-metrics">
              <div className="other-metrics-box">
                <div className="db-retriever-latency-wrapper">
                  <div className="db-retriever-latency-name">Embedding + DB Retriever Latency</div>
                  <div className="db-retriever-latency-value">
                    {convertValue(metrics.retriver_latency)}
                  </div>
                </div>
                <div className="db-retriever-latency-wrapper">
                  <div className="db-retriever-latency-name">
                    Vector&nbsp;DB
                    <br />
                    Throughput
                  </div>
                  <div className="db-retriever-latency-value">2.35x</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      <footer className="disclaimer">
        <p>
          Visit Vision 2024 Section of www.intel.com/performanceindex for workloads and
          configurations. Results may vary.
        </p>
      </footer>
    </main>
  );
};

export default TelemetryPage;
