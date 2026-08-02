"use client";

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  IconSparkles,
  IconTrendingUp,
  IconPackage,
  IconMessageChatbot,
  IconArrowRight,
  IconCpu,
  IconCheck,
  IconChartBar,
  IconUpload
} from "@tabler/icons-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0c0d10] text-slate-100 font-sans antialiased selection:bg-indigo-600 selection:text-white">
      
      {/* GLOWING AMBIENT BACKGROUND */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-200 h-100 bg-linear-to-b from-indigo-600/20 via-purple-600/10 to-transparent blur-[140px]"></div>
      </div>

      {/* STICKY TOP NAVBAR */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-[#0c0d10]/80 border-b border-[#1e2029] px-6 lg:px-16 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-linear-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white font-black text-lg shadow-lg shadow-indigo-600/30">
            S
          </div>
          <div>
            <h1 className="font-bold text-white text-base tracking-tight leading-none flex items-center gap-1">Stoq</h1>
          </div>
        </div>

        <nav className="hidden md:flex items-center gap-8 text-xs font-semibold text-slate-400">
          <a href="#features" className="hover:text-white transition-colors">Features</a>
          <a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a>
          <a href="#benchmarks" className="hover:text-white transition-colors">Benchmarks</a>
        </nav>

        <Link
          href="/dashboard"
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-xl text-xs font-bold shadow-md shadow-indigo-600/30 flex items-center gap-2 transition-all duration-200 hover:scale-[1.02]"
        >
          <span>Launch Dashboard</span>
          <IconArrowRight size={16} />
        </Link>
      </header>

      {/* HERO SECTION */}
      <section className="relative z-10 pt-36 pb-32 px-6 lg:px-16 max-w-5xl mx-auto text-center flex flex-col items-center">
        
        {/* Subtle AI Badge */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-bold mb-6"
        >
          <IconSparkles size={14} className="text-indigo-400 animate-pulse" />
          <span>AI Demand Forecasting & Inventory Agent</span>
        </motion.div>

        {/* Main Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight text-white leading-[1.1]"
        >
          Predict Demand. <br />
          <span className="bg-linear-to-r from-indigo-400 via-violet-400 to-indigo-400 bg-clip-text text-transparent">
            Eliminate Stockouts.
          </span>
        </motion.h1>

        {/* Concise Description */}
        <motion.p
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="mt-6 text-base sm:text-lg text-slate-400 max-w-2xl font-medium leading-relaxed"
        >
          RetailPilot AI ingests point-of-sale sales data, trains product-level XGBoost time-series regressors, maintains 2.5 days of safety stock, and provides real-time AI store co-piloting.
        </motion.p>

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
          className="mt-10 flex flex-wrap justify-center items-center gap-4"
        >
          <Link
            href="/dashboard"
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3.5 rounded-xl text-xs font-bold shadow-lg shadow-indigo-600/30 flex items-center gap-2 transition-all duration-200 hover:scale-[1.02]"
          >
            <span>Open AI Dashboard</span>
            <IconArrowRight size={16} />
          </Link>
          <a
            href="#features"
            className="bg-[#13141b] hover:bg-[#1c1d27] text-slate-300 border border-[#1e2029] px-7 py-3.5 rounded-xl text-xs font-semibold transition-all duration-200"
          >
            View Features
          </a>
        </motion.div>

      </section>

      {/* CORE FEATURES SECTION */}
      <section id="features" className="py-20 px-6 lg:px-16 max-w-6xl mx-auto border-t border-[#1e2029]">
        <div className="text-center max-w-2xl mx-auto mb-14">
          <h2 className="text-xs font-bold uppercase tracking-widest text-indigo-400 mb-2">Capabilities</h2>
          <p className="text-2xl sm:text-4xl font-black text-white tracking-tight">
            Built for Modern Retail Operations
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[
            {
              icon: <IconCpu className="text-indigo-400" size={24} />,
              title: "XGBoost Demand Forecasting",
              desc: "Product-level gradient boosted regressors built with 7-day sales lags, rolling averages, and day-of-week seasonality multipliers."
            },
            {
              icon: <IconPackage className="text-emerald-400" size={24} />,
              title: "Order-Up-To Replenishment",
              desc: "Calculates precise order quantities to maintain a 2.5-day safety stock buffer and eliminate out-of-stock occurrences."
            },
            {
              icon: <IconMessageChatbot className="text-violet-400" size={24} />,
              title: "Live AI Store Assistant",
              desc: "Natural language co-pilot ingesting real-time store database context to answer queries on stock alerts, reorders, and forecasts."
            },
            {
              icon: <IconChartBar className="text-amber-400" size={24} />,
              title: "Out-of-Sample Holdout Testing",
              desc: "Evaluated on a 20% holdout test set across 2,160 real sales records to validate accuracy and stockout mitigation."
            }
          ].map((feat, idx) => (
            <div
              key={idx}
              className="bg-[#13141b] border border-[#1e2029] rounded-2xl p-6 shadow-xl flex items-start gap-4"
            >
              <div className="p-3 rounded-xl bg-[#1c1d27] border border-[#2e3142] shrink-0">
                {feat.icon}
              </div>
              <div>
                <h3 className="text-sm font-bold text-white mb-1">{feat.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed font-medium">{feat.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* HOW IT WORKS SECTION */}
      <section id="how-it-works" className="py-20 px-6 lg:px-16 max-w-6xl mx-auto border-t border-[#1e2029]">
        <div className="text-center max-w-2xl mx-auto mb-14">
          <h2 className="text-xs font-bold uppercase tracking-widest text-indigo-400 mb-2">Workflow</h2>
          <p className="text-2xl sm:text-4xl font-black text-white tracking-tight">
            Simple 3-Step Store Automation
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { step: "01", title: "Ingest Sales CSV", desc: "Upload POS sales history or download our sample CSV template." },
            { step: "02", title: "XGBoost ML Retraining", desc: "Feature engineering constructs lags, moving averages, and reorder forecasts." },
            { step: "03", title: "AI Store Co-Pilot", desc: "Get recommended reorder quantities and chat with your store AI co-pilot." },
          ].map((item, idx) => (
            <div key={idx} className="bg-[#13141b] border border-[#1e2029] rounded-2xl p-6 shadow-xl relative">
              <span className="text-3xl font-black text-indigo-400/20 block mb-2 font-mono">{item.step}</span>
              <h3 className="text-sm font-bold text-white mb-1">{item.title}</h3>
              <p className="text-xs text-slate-400 font-medium leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* BENCHMARK COMPARISON TABLE */}
      <section id="benchmarks" className="py-20 px-6 lg:px-16 max-w-4xl mx-auto border-t border-[#1e2029]">
        <div className="bg-[#13141b] border border-[#1e2029] rounded-3xl p-8 shadow-xl">
          <div className="text-center mb-6">
            <h3 className="text-lg font-bold text-white">Algorithm Benchmark Comparison</h3>
            <p className="text-xs text-slate-400 mt-1">Evaluated on 20% holdout test dataset (180 historical days)</p>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[#1e2029] text-[10px] text-slate-400 font-bold uppercase">
                  <th className="pb-3">Algorithm</th>
                  <th className="pb-3 text-center">MAE Error</th>
                  <th className="pb-3 text-center">WAPE Error</th>
                  <th className="pb-3 text-right">Overall Accuracy</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1e2029] font-medium">
                <tr className="text-slate-300">
                  <td className="py-3.5 font-semibold text-white">7-Day Moving Average</td>
                  <td className="py-3.5 text-center">4.24</td>
                  <td className="py-3.5 text-center">25.7%</td>
                  <td className="py-3.5 text-right">74.3%</td>
                </tr>
                <tr className="text-slate-300">
                  <td className="py-3.5 font-semibold text-white">Linear Regression</td>
                  <td className="py-3.5 text-center">3.33</td>
                  <td className="py-3.5 text-center">20.3%</td>
                  <td className="py-3.5 text-right">79.7%</td>
                </tr>
                <tr className="bg-indigo-500/10 text-white font-bold border-l-4 border-indigo-500">
                  <td className="py-3.5 pl-3 text-indigo-300">RetailPilot XGBoost</td>
                  <td className="py-3.5 text-center">3.83</td>
                  <td className="py-3.5 text-center text-emerald-400">23.3%</td>
                  <td className="py-3.5 text-right text-indigo-400">82.1%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* CTA BANNER & FOOTER */}
      <footer className="border-t border-[#1e2029] py-12 px-6 lg:px-16 text-center text-xs text-slate-500 space-y-6">
        <div className="flex justify-center">
          <Link
            href="/dashboard"
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3.5 rounded-xl text-xs font-bold shadow-lg shadow-indigo-600/30 flex items-center gap-2 transition-all duration-200 hover:scale-105"
          >
            <span>Launch Dashboard Now</span>
            <IconArrowRight size={16} />
          </Link>
        </div>
        <p className="text-slate-400 font-medium">RetailPilot AI © 2026. All rights reserved.</p>
      </footer>

    </div>
  );
}
