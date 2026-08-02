"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const router = useRouter();

  async function uploadFile() {
    if (!file) return;

    setLoading(true);
    setMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await api.post("/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setMessage(res.data.message || "Upload successful! Redirecting to Dashboard...");
      // Re-trigger predictions after successful upload
      await api.post("/predictions");
      
      setTimeout(() => {
        router.push("/dashboard");
      }, 1500);
    } catch (err: any) {
      console.error(err);
      const errMsg = err.response?.data?.detail?.message || err.response?.data?.detail || "Upload failed.";
      setMessage(errMsg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#0c0d10] flex items-center justify-center text-slate-100 p-6 selection:bg-indigo-600 selection:text-white">
      <div className="bg-[#13141b] border border-[#1e2029] p-10 rounded-3xl w-full max-w-lg shadow-2xl space-y-6">

        <div className="flex items-center justify-between border-b border-[#1e2029] pb-4">
          <div>
            <h1 className="text-xl font-black text-white">
              Upload Sales CSV
            </h1>
            <p className="text-xs text-slate-400 mt-1 font-medium">Ingest point-of-sale data to retrain XGBoost models</p>
          </div>

          <a
            href="/sample_retail_sales.csv"
            download="sample_retail_sales.csv"
            className="bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-400 border border-indigo-500/30 px-3.5 py-2 rounded-xl text-xs font-bold transition-all duration-200 flex items-center gap-1.5 shadow-sm"
          >
            <span>Download Sample CSV</span>
          </a>
        </div>

        <div className="border-2 border-dashed border-[#2e3142] rounded-2xl p-6 text-center space-y-3">
          <input
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-xs text-slate-400 file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:font-bold file:bg-indigo-500/20 hover:file:bg-indigo-500/30 cursor-pointer"
          />
          <p className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">
            Headers: product_name, sku, category, sale_date, quantity_sold, price, current_stock, reorder_point
          </p>
        </div>

        <button
          onClick={uploadFile}
          disabled={loading || !file}
          className="w-full hover:bg-indigo-700 disabled:bg-indigo-900 text-white rounded-xl py-3 text-xs font-bold transition-all shadow-md shadow-indigo-600/30"
        >
          {loading ? "Uploading & Retraining..." : "Upload CSV & Forecast Sales"}
        </button>

        {message && (
          <div className="p-4 rounded-xl text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            {message}
          </div>
        )}

      </div>
    </main>
  );
}