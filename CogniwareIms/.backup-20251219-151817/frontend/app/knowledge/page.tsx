// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

"use client";

import React, { useState, useEffect } from "react";
import {
  Database,
  Upload,
  RefreshCw,
  Search,
  TrendingUp,
  Cpu,
} from "lucide-react";
import FileUpload from "../../components/FileUpload";

interface KnowledgeStats {
  total_documents: number;
  last_update: string | null;
  training_runs: number;
  recent_runs: any[];
}

export default function KnowledgePage() {
  const [activeTab, setActiveTab] = useState<"upload" | "manage" | "search">(
    "upload",
  );
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [retraining, setRetraining] = useState(false);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await fetch("/api/knowledge/stats");
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error("Error loading stats:", error);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setSearching(true);
    try {
      const response = await fetch(
        `/api/knowledge/search?q=${encodeURIComponent(searchQuery)}&top_k=5`,
      );
      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (error) {
      console.error("Search error:", error);
    } finally {
      setSearching(false);
    }
  };

  const handleRetrain = async () => {
    setRetraining(true);
    try {
      const response = await fetch("/api/knowledge/retrain", {
        method: "POST",
      });
      const data = await response.json();

      if (data.success) {
        await loadStats();
        alert(
          `✅ Successfully retrained ${data.documents_retrained} documents!`,
        );
      } else {
        alert("❌ Retraining failed");
      }
    } catch (error) {
      console.error("Retrain error:", error);
      alert("❌ Retraining error");
    } finally {
      setRetraining(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header with Intel Xeon Badge */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-black mb-2">
                Knowledge Base Management
              </h1>
              <p className="text-black">
                Powered by OPEA AI on{" "}
                <span className="inline-flex items-center gap-2 font-semibold text-blue-600">
                  <Cpu size={20} />
                  Intel Xeon Processors
                </span>
              </p>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={loadStats}
                className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg font-semibold hover:bg-blue-200 transition-all flex items-center gap-2"
              >
                <RefreshCw size={18} />
                Refresh
              </button>
            </div>
          </div>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <Database size={32} className="text-blue-600 mb-2" />
            <div className="text-3xl font-bold text-black">
              {stats?.total_documents || 0}
            </div>
            <div className="text-sm text-black">Total Documents</div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <TrendingUp size={32} className="text-green-600 mb-2" />
            <div className="text-3xl font-bold text-black">
              {stats?.training_runs || 0}
            </div>
            <div className="text-sm text-black">Training Runs</div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <Upload size={32} className="text-purple-600 mb-2" />
            <div className="text-3xl font-bold text-black">
              {stats?.recent_runs?.length || 0}
            </div>
            <div className="text-sm text-black">Recent Updates</div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <Cpu size={32} className="text-blue-600 mb-2" />
            <div className="text-2xl font-bold text-black">Active</div>
            <div className="text-sm text-black">Intel Xeon System</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab("upload")}
              className={`flex-1 px-6 py-4 font-semibold transition-all ${
                activeTab === "upload"
                  ? "bg-blue-50 text-blue-700 border-b-2 border-blue-600"
                  : "text-black hover:bg-gray-50"
              }`}
            >
              <Upload size={20} className="inline mr-2" />
              Upload Files
            </button>
            <button
              onClick={() => setActiveTab("search")}
              className={`flex-1 px-6 py-4 font-semibold transition-all ${
                activeTab === "search"
                  ? "bg-blue-50 text-blue-700 border-b-2 border-blue-600"
                  : "text-black hover:bg-gray-50"
              }`}
            >
              <Search size={20} className="inline mr-2" />
              Search Knowledge
            </button>
            <button
              onClick={() => setActiveTab("manage")}
              className={`flex-1 px-6 py-4 font-semibold transition-all ${
                activeTab === "manage"
                  ? "bg-blue-50 text-blue-700 border-b-2 border-blue-600"
                  : "text-black hover:bg-gray-50"
              }`}
            >
              <Database size={20} className="inline mr-2" />
              Manage
            </button>
          </div>

          <div className="p-6">
            {activeTab === "upload" && <FileUpload />}

            {activeTab === "search" && (
              <div className="space-y-6">
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                    placeholder="Search knowledge base..."
                    className="flex-1 px-4 py-3 border border-gray-200 rounded-lg text-black focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button
                    onClick={handleSearch}
                    disabled={searching}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-all disabled:opacity-50 flex items-center gap-2"
                  >
                    {searching ? (
                      <>
                        <RefreshCw size={20} className="animate-spin" />
                        Searching...
                      </>
                    ) : (
                      <>
                        <Search size={20} />
                        Search
                      </>
                    )}
                  </button>
                </div>

                {searchResults.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="text-xl font-bold text-black">
                      Found {searchResults.length} results
                    </h3>
                    {searchResults.map((result, idx) => (
                      <div
                        key={idx}
                        className="p-4 bg-gray-50 rounded-lg border border-gray-200"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <span className="text-sm font-semibold text-blue-600">
                            Relevance: {(result.score * 100).toFixed(1)}%
                          </span>
                          <span className="text-xs text-black">
                            {result.metadata?.source || "Unknown source"}
                          </span>
                        </div>
                        <p className="text-black">{result.text}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === "manage" && (
              <div className="space-y-6">
                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  <h3 className="text-xl font-bold text-black mb-4">
                    Retrain Knowledge Base
                  </h3>
                  <p className="text-black mb-4">
                    Retrain the entire knowledge base with new embeddings. This
                    ensures all data is indexed with the latest model. Optimized
                    for Intel Xeon processors.
                  </p>
                  <button
                    onClick={handleRetrain}
                    disabled={retraining}
                    className="px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg font-semibold hover:from-green-700 hover:to-emerald-700 transition-all disabled:opacity-50 flex items-center gap-2"
                  >
                    <RefreshCw
                      size={20}
                      className={retraining ? "animate-spin" : ""}
                    />
                    {retraining ? "Retraining..." : "Retrain Knowledge Base"}
                  </button>
                </div>

                {stats && stats.recent_runs && stats.recent_runs.length > 0 && (
                  <div className="bg-white rounded-xl border border-gray-200 p-6">
                    <h3 className="text-xl font-bold text-black mb-4">
                      Recent Training Runs
                    </h3>
                    <div className="space-y-2">
                      {stats.recent_runs.map((run: any, idx: number) => (
                        <div
                          key={idx}
                          className="p-3 bg-gray-50 rounded-lg border border-gray-200"
                        >
                          <div className="flex justify-between items-center">
                            <div>
                              <div className="text-sm font-semibold text-black">
                                {run.source || run.type}
                              </div>
                              <div className="text-xs text-black">
                                {run.documents_added || run.documents_processed}{" "}
                                documents
                              </div>
                            </div>
                            <div className="text-xs text-black">
                              {new Date(run.timestamp).toLocaleString()}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Intel Xeon Info */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-6 text-white shadow-lg">
          <div className="flex items-start gap-4">
            <Cpu size={48} className="flex-shrink-0" />
            <div>
              <h3 className="text-2xl font-bold mb-2">
                Intel Xeon Performance
              </h3>
              <p className="text-white/90 mb-4">
                This system leverages Intel Xeon processors with AI acceleration
                for superior knowledge processing performance:
              </p>
              <ul className="space-y-2 text-white/90">
                <li className="flex items-start gap-2">
                  <span className="text-yellow-300 font-bold">⚡</span>
                  <span>
                    Optimized embedding generation with Intel libraries
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-yellow-300 font-bold">⚡</span>
                  <span>
                    Fast vector similarity search powered by Intel optimizations
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-yellow-300 font-bold">⚡</span>
                  <span>
                    Efficient document processing with Intel Xeon compute power
                  </span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
