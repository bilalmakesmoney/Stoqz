"use client";

import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  IconLayoutDashboard,
  IconPackage,
  IconTrendingUp,
  IconSparkles,
  IconSearch,
  IconBell,
  IconUpload,
  IconLoader2,
  IconAlertTriangle,
  IconCheck,
  IconRefresh,
  IconSend,
  IconMessageChatbot
} from "@tabler/icons-react";
import { api } from "@/lib/api";
import {
  AreaChart,
  Area,
  XAxis,
  Tooltip,
  ResponsiveContainer
} from "recharts";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [notificationsOpen, setNotificationsOpen] = useState<boolean>(false);
  const [isMounted, setIsMounted] = useState<boolean>(false);
  
  // Inventory view states
  const [inventoryList, setInventoryList] = useState<any[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [restockingProduct, setRestockingProduct] = useState<string | null>(null);
  const [restockQty, setRestockQty] = useState<string>("50");
  
  // Predictions view states
  const [expandedExplanations, setExpandedExplanations] = useState<Record<string, boolean>>({});
  const [runPredictionLoading, setRunPredictionLoading] = useState<boolean>(false);
  const [runPredictionSuccess, setRunPredictionSuccess] = useState<boolean>(false);
  
  // Upload states
  const [file, setFile] = useState<File | null>(null);
  const [uploadLoading, setUploadLoading] = useState<boolean>(false);
  const [uploadMessage, setUploadMessage] = useState<string>("");
  const [uploadSuccess, setUploadSuccess] = useState<boolean>(false);



  // Assistant Chatbot states
  const [chatMessages, setChatMessages] = useState<Array<{ sender: "user" | "assistant"; text: string; time: string }>>([
    {
      sender: "assistant",
      text: "Hello! 👋 I am **Stoq AI Assistant**, your intelligent retail store co-pilot.\n\nAsk me anything about store inventory, tomorrow's demand forecasts, recommended reorder quantities, or ML model accuracy!",
      time: "Just now",
    },
  ]);
  const [chatInput, setChatInput] = useState<string>("");
  const [chatLoading, setChatLoading] = useState<boolean>(false);

  async function handleSendChatMessage(textToSend?: string) {
    const query = (textToSend || chatInput).trim();
    if (!query || chatLoading) return;

    const timeNow = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const userMsg = { sender: "user" as const, text: query, time: timeNow };
    
    setChatMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setChatInput("");
    setChatLoading(true);

    try {
      const res = await api.post("/insights/assistant", { message: query });
      const assistantMsg = {
        sender: "assistant" as const,
        text: res.data.reply || "I have analyzed your retail dataset.",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setChatMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error("Chatbot error:", err);
      setChatMessages((prev) => [
        ...prev,
        {
          sender: "assistant" as const,
          text: "⚠️ Sorry, I encountered an issue connecting to the AI engine. Please verify backend server status.",
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  }

  useEffect(() => {
    setIsMounted(true);
    loadMetrics();
  }, []);

  async function loadMetrics() {
    setLoading(true);
    try {
      const res = await api.get("/dashboard/metrics");
      setMetrics(res.data);
      
      // Load full inventory list
      const invRes = await api.get("/analytics/inventory-status");
      setInventoryList(invRes.data);
    } catch (err) {
      console.error("Error loading metrics:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleRunPredictions() {
    setRunPredictionLoading(true);
    setRunPredictionSuccess(false);
    try {
      await api.post("/predictions");
      setRunPredictionSuccess(true);
      setTimeout(() => setRunPredictionSuccess(false), 3000);
      await loadMetrics();
    } catch (err) {
      console.error("Error running predictions:", err);
    } finally {
      setRunPredictionLoading(false);
    }
  }

  async function handleRestock(productName: string, quantity: number) {
    try {
      await api.post(`/dashboard/restock?product_name=${encodeURIComponent(productName)}&quantity=${quantity}`);
      await loadMetrics();
    } catch (err) {
      console.error("Error restocking product:", err);
    }
  }

  async function handleUploadCSV() {
    if (!file) return;
    setUploadLoading(true);
    setUploadMessage("");
    setUploadSuccess(false);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await api.post("/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setUploadSuccess(true);
      setUploadMessage(res.data.message || "Sales data uploaded successfully! Redirecting to Dashboard...");
      // Re-trigger predictions after successful upload to update ML models
      await api.post("/predictions");
      await loadMetrics();
      setFile(null);
      setTimeout(() => {
        setActiveTab("dashboard");
        setUploadMessage("");
        setUploadSuccess(false);
      }, 1500);
    } catch (err: any) {
      console.error("Upload error:", err);
      const errMsg = err.response?.data?.detail?.message || err.response?.data?.detail || "Upload failed. Please verify the CSV format.";
      setUploadMessage(errMsg);
    } finally {
      setUploadLoading(false);
    }
  }

  if (loading || !metrics) {
    return (
      <main className="h-screen bg-[#0c0d10] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <IconLoader2 className="animate-spin text-indigo-400" size={40} />
          <p className="text-gray-700 font-medium">Loading Stoqz...</p>
        </div>
      </main>
    );
  }

  // Filter products needing reorder
  const filteredReorderItems = metrics.reorder_items.filter((item: any) =>
    item.product_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.sku.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Filter recent predictions
  const filteredPredictions = metrics.recent_predictions.filter((item: any) =>
    item.product_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Filter full inventory list
  const filteredInventory = inventoryList.filter((item: any) => {
    const matchesSearch = item.product.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === "All" || 
      (selectedCategory === "Beverages" && item.product.includes("Water") || item.product.includes("Juice") || item.product.includes("Tea") || item.product.includes("Cola")) ||
      (selectedCategory === "Snacks" && item.product.includes("Bread") || item.product.includes("Chips") || item.product.includes("Cookies") || item.product.includes("Nuts") || item.product.includes("Pretzels")) ||
      (selectedCategory === "Dairy" && item.product.includes("Milk") || item.product.includes("Butter") || item.product.includes("Cheese") || item.product.includes("Yogurt")) ||
      (selectedCategory === "Produce" && item.product.includes("Banana") || item.product.includes("Strawberr") || item.product.includes("Apple") || item.product.includes("Spinach") || item.product.includes("Avocado")) ||
      (selectedCategory === "Household" && item.product.includes("Towels") || item.product.includes("Soap") && item.product.includes("Dish") || item.product.includes("Detergent") || item.product.includes("Bags")) ||
      (selectedCategory === "Personal Care" && item.product.includes("Hand") || item.product.includes("Toothpaste"));
    
    return matchesSearch && (selectedCategory === "All" || matchesCategory);
  });

  return (
    <div className="min-h-screen bg-[#0c0d10] flex font-sans antialiased text-slate-100 selection:bg-indigo-600 selection:text-white">
      
      {/* SIDEBAR */}
      <aside className="w-64 bg-[#13141b] border-r border-[#1e2029] flex flex-col justify-between p-6 sticky top-0 h-screen shrink-0">
        <div>
          {/* Logo */}
          <div className="flex items-center gap-3 mb-8 select-none">
            <div className="w-9 h-9 rounded-xl bg-linear-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white font-black text-lg shadow-lg shadow-indigo-600/30">
              S
            </div>
            <div>
              <h1 className="font-black text-white text-base tracking-tight leading-none">Stoqz</h1>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1.5">
            {[
              { id: "dashboard", label: "Dashboard", icon: <IconLayoutDashboard size={20} /> },
              { id: "inventory", label: "Inventory", icon: <IconPackage size={20} /> },
              { id: "predictions", label: "Predictions", icon: <IconTrendingUp size={20} /> },
              { id: "assistant", label: "AI Assistant", icon: <IconMessageChatbot size={20} /> },
            ].map((link) => (
              <button
                key={link.id}
                onClick={() => {
                  setActiveTab(link.id);
                  setSearchQuery("");
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-xs font-bold transition-all duration-200 ${
                  activeTab === link.id
                    ? "bg-white text-slate-950 shadow-lg shadow-white/10"
                    : "text-slate-400 hover:bg-[#1a1b24] hover:text-white"
                }`}
              >
                {link.icon}
                {link.label}
              </button>
            ))}
          </nav>
        </div>
      </aside>

      {/* MAIN CONTAINER */}
      <div className="flex-1 flex flex-col min-w-0">
        
        {/* TOP BAR */}
        <header className="h-20 bg-[#0c0d10] border-b border-[#1e2029] px-8 flex items-center justify-between z-10 sticky top-0 backdrop-blur-md">
          <div>
            <h2 className="font-black text-white text-lg capitalize tracking-tight">{activeTab}</h2>
            <p className="text-xs text-slate-400 font-medium">{metrics.today_date}</p>
          </div>

          <div className="flex items-center gap-6">
            {/* Search Input */}
            <div className="relative w-64">
              <IconSearch className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
              <input
                type="text"
                placeholder="Search products..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-[#13141b] border rounded-xl text-xs placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 transition-all duration-200"
              />
            </div>

            {/* Notification Bell */}
            <div className="relative">
              <button 
                onClick={() => setNotificationsOpen(!notificationsOpen)}
                className="w-10 h-10 rounded-xl bg-[#13141b] border border-[#1e2029] flex items-center justify-center text-slate-300 hover:text-white hover:bg-[#1c1d27] transition-all duration-200 relative"
              >
                <IconBell size={20} />
                {metrics.reorder_items.length > 0 && (
                  <span className="absolute top-2 right-2.5 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-[#0c0d10]"></span>
                )}
              </button>

              <AnimatePresence>
                {notificationsOpen && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setNotificationsOpen(false)}></div>
                    <motion.div
                      initial={{ opacity: 0, y: 10, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 10, scale: 0.95 }}
                      className="absolute right-0 mt-2 w-80 bg-[#13141b] border border-[#1e2029] shadow-2xl rounded-2xl p-4 z-50 max-h-100 overflow-y-auto"
                    >
                      <h3 className="font-bold text-sm text-white mb-3 flex items-center justify-between">
                        Alerts & Notifications
                        <span className="px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[10px] font-bold">
                          {metrics.reorder_items.length} Urgently Needed
                        </span>
                      </h3>
                      <div className="space-y-2">
                        {metrics.reorder_items.map((item: any, idx: number) => (
                          <div key={idx} className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-xs flex gap-2">
                            <IconAlertTriangle className="text-rose-400 shrink-0 mt-0.5" size={16} />
                            <div>
                              <p className="font-semibold text-white">{item.product_name}</p>
                              <p className="text-slate-400 mt-0.5">
                                Stock is at <strong className="text-rose-400">{item.current_stock}</strong>. Suggesting reorder of {item.suggested} units.
                              </p>
                            </div>
                          </div>
                        ))}
                        {metrics.reorder_items.length === 0 && (
                          <p className="text-slate-400 text-center py-4">No critical alerts found.</p>
                        )}
                      </div>
                    </motion.div>
                  </>
                )}
              </AnimatePresence>
            </div>

            {/* Profile User */}
            <div className="flex items-center gap-3 border-l border-[#1e2029] pl-6 select-none">
              <div className="text-right">
                <p className="font-bold text-white text-sm leading-none">Muhammad Bilal</p>
                <span className="text-[10px] text-slate-400 font-semibold">Green Valley Market</span>
              </div>
              <div className="w-9 h-9 rounded-full bg-linear-to-br from-indigo-500 to-violet-600 text-white flex items-center justify-center font-bold text-xs shadow-md shadow-indigo-600/20">
                MB
              </div>
            </div>
          </div>
        </header>

        {/* CONTENT PANELS CONTAINER */}
        <main className="flex-1 p-8 overflow-y-auto max-w-350 w-full mx-auto">
          <AnimatePresence mode="wait">
            
            {/* VIEW 1: DASHBOARD */}
            {activeTab === "dashboard" && (
              <motion.div
                key="dashboard"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.2 }}
                className="space-y-8"
              >
                {/* KPI Metrics row */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {[
                    {
                      title: "TODAY'S REVENUE",
                      value: metrics.kpi.revenue.value,
                      change: metrics.kpi.revenue.change,
                      positive: !metrics.kpi.revenue.change.includes("-"),
                      badge: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
                    },
                    {
                      title: "PRODUCTS IN STOCK",
                      value: metrics.kpi.stock.value,
                      change: metrics.kpi.stock.change,
                      positive: !metrics.kpi.stock.change.includes("-"),
                      badge: "bg-rose-500/20 text-rose-400 border-rose-500/30",
                    },
                    {
                      title: "ITEMS TO REORDER",
                      value: metrics.kpi.reorder.value,
                      change: metrics.kpi.reorder.change,
                      positive: true,
                      badge: "bg-amber-500/20 text-amber-400 border-amber-500/30",
                    },
                    {
                      title: "PREDICTION ACCURACY",
                      value: metrics.kpi.accuracy.value,
                      change: metrics.kpi.accuracy.change,
                      positive: !metrics.kpi.accuracy.change.includes("-"),
                      badge: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30",
                    },
                  ].map((card, idx) => (
                    <div
                      key={idx}
                      className="bg-[#13141b] border border-[#1e2029] rounded-3xl p-6 shadow-xl hover:border-slate-700 transition-all duration-300 flex flex-col justify-between min-h-35"
                    >
                      <div className="flex justify-between items-center">
                        <h4 className="text-[10px] text-slate-400 font-bold tracking-widest uppercase">{card.title}</h4>
                        <div className="w-7 h-7 rounded-full bg-white/10 text-white flex items-center justify-center text-xs">
                          ↗
                        </div>
                      </div>
                      <div className="mt-3 flex items-baseline justify-between">
                        <span className="text-3xl font-black text-white tracking-tight">{card.value}</span>
                      </div>
                      <div className="mt-2 flex items-center">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${card.badge}`}>
                          {card.change}
                        </span>
                        <span className="text-[10px] text-slate-500 font-medium ml-1.5">vs yesterday</span>
                      </div>
                    </div>
                  ))}
                </div>

                {metrics.is_empty ? (
                  <div className="bg-[#13141b] border border-[#1e2029] rounded-3xl p-12 text-center max-w-2xl mx-auto flex flex-col items-center justify-center gap-6 shadow-2xl mt-8">
                    <div className="w-16 h-16 rounded-full bg-indigo-500/20 border border-indigo-500/30 text-indigo-400 flex items-center justify-center font-bold text-2xl">
                      AI
                    </div>
                    <div className="space-y-2">
                      <h3 className="font-bold text-white text-lg">Initialize your Forecasting Dashboard</h3>
                      <p className="text-sm text-slate-400 max-w-md leading-relaxed mx-auto">
                        No sales records are currently present in your inventory catalog database. Upload your POS daily sales history to generate demand predictions, reorder points, and category stock status.
                      </p>
                    </div>
                    <button
                      onClick={() => setActiveTab("upload")}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-xl text-sm font-bold shadow-lg shadow-indigo-600/30 flex items-center gap-2 select-none transition-all duration-200"
                    >
                      <IconUpload size={18} />
                      Upload sales history CSV
                    </button>
                  </div>
                ) : (
                  <>
                    {/* MIDDLE ROW: Sales Trend & Inventory Status */}
                    <div className="grid lg:grid-cols-5 gap-8">
                  {/* Sales Trend Chart */}
                  <div className="lg:col-span-3 bg-[#13141b] border border-[#1e2029] rounded-3xl p-6 shadow-xl">
                    <div className="flex justify-between items-center mb-6">
                      <div>
                        <h3 className="font-bold text-white text-sm">Sales Trend</h3>
                        <p className="text-xs text-slate-400">Daily revenue over the past 7 days</p>
                      </div>
                    </div>
                    
                    <div className="h-70">
                      {isMounted && (
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={metrics.sales_trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                            <defs>
                              <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                                <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0}/>
                              </linearGradient>
                            </defs>
                            <XAxis 
                              dataKey="name" 
                              axisLine={false} 
                              tickLine={false} 
                              tick={{ fill: '#64748b', fontSize: 11, fontWeight: 500 }} 
                            />
                            <Tooltip 
                              contentStyle={{ background: '#1c1d27', border: '1px solid #2e3142', borderRadius: '14px', color: '#fff' }}
                              labelStyle={{ color: '#94a3b8', fontWeight: 600 }}
                              formatter={(value: any) => [`₹${value.toLocaleString()}`, 'Revenue']}
                            />
                            <Area 
                              type="monotone" 
                              dataKey="revenue" 
                              stroke="#6366f1" 
                              strokeWidth={3} 
                              fillOpacity={1} 
                              fill="url(#colorRevenue)" 
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      )}
                    </div>
                  </div>

                  {/* Inventory Status stacked progress bars */}
                  <div className="lg:col-span-2 bg-[#13141b] border border-[#1e2029] rounded-3xl p-6 shadow-xl flex flex-col justify-between">
                    <div>
                      <h3 className="font-bold text-white text-sm">Inventory Status</h3>
                      <p className="text-xs text-slate-400 mb-6">Stock levels by category</p>
                      
                      <div className="space-y-4">
                        {metrics.inventory_status.map((item: any, idx: number) => (
                          <div key={idx} className="space-y-1.5">
                            <div className="flex justify-between items-center text-xs font-semibold">
                              <span className="text-slate-200">{item.category}</span>
                              <span className="text-slate-400 font-bold">{item.total} items</span>
                            </div>
                            {/* Segmented bar */}
                            <div className="h-3 w-full bg-[#1c1d27] rounded-full overflow-hidden flex">
                              <div style={{ width: `${item.in_stock}%` }} className="bg-emerald-500 h-full transition-all duration-300"></div>
                              <div style={{ width: `${item.low}%` }} className="bg-amber-400 h-full transition-all duration-300"></div>
                              <div style={{ width: `${item.out}%` }} className="bg-rose-500 h-full transition-all duration-300"></div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Progress Bar Legend */}
                    <div className="flex gap-4 items-center justify-center border-t border-[#1e2029] pt-4 mt-4 text-[10px] font-bold text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                        In Stock
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
                        Low
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                        Out
                      </div>
                    </div>
                  </div>
                </div>

                {/* BOTTOM ROW: Tables */}
                <div className="grid lg:grid-cols-2 gap-8">
                  {/* Products Needing Reorder */}
                  <div className="bg-[#13141b] border border-[#1e2029] rounded-3xl p-6 shadow-xl overflow-hidden">
                    <h3 className="font-bold text-white text-sm">Products Needing Reorder</h3>
                    <p className="text-xs text-slate-400 mb-6">Items below reorder threshold</p>
                    
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="text-[10px] text-slate-400 font-bold border-b border-[#1e2029]">
                            <th className="pb-3 w-[45%]">PRODUCT</th>
                            <th className="pb-3 text-center">STOCK</th>
                            <th className="pb-3 text-center">REORDER AT</th>
                            <th className="pb-3 text-center text-indigo-400">SUGGESTED</th>
                            <th className="pb-3 text-right">STATUS</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredReorderItems.map((item: any, idx: number) => (
                            <tr key={idx} className="border-b border-[#1a1b24] hover:bg-[#1a1b24] transition-colors duration-150">
                              <td className="py-3">
                                <p className="font-bold text-white text-xs">{item.product_name}</p>
                                <span className="text-[9px] text-slate-500 font-semibold tracking-wider uppercase">{item.sku}</span>
                              </td>
                              <td className="py-3 text-center font-bold text-slate-200 text-xs">{item.current_stock}</td>
                              <td className="py-3 text-center text-slate-400 text-xs font-semibold">{item.reorder_point}</td>
                              <td className="py-3 text-center font-bold text-indigo-400 text-xs">{item.suggested}</td>
                              <td className="py-3 text-right">
                                <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                                  item.status === "Out of Stock" 
                                    ? "bg-rose-500/20 text-rose-400 border-rose-500/30" 
                                    : "bg-amber-500/20 text-amber-400 border-amber-500/30"
                                }`}>
                                  {item.status}
                                </span>
                              </td>
                            </tr>
                          ))}
                          {filteredReorderItems.length === 0 && (
                            <tr>
                              <td colSpan={5} className="py-8 text-center text-slate-500 text-xs font-medium">
                                No products found needing reorder.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Recent Predictions */}
                  <div className="bg-[#13141b] border border-[#1e2029] rounded-3xl p-6 shadow-xl overflow-hidden">
                    <h3 className="font-bold text-white text-sm">Recent Predictions</h3>
                    <p className="text-xs text-slate-400 mb-6">AI demand forecasts vs actuals</p>
                    
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="text-[10px] text-slate-400 font-bold border-b border-[#1e2029]">
                            <th className="pb-3 w-[40%]">PRODUCT</th>
                            <th className="pb-3 text-center">PREDICTED</th>
                            <th className="pb-3 text-center">ACTUAL</th>
                            <th className="pb-3 text-center text-indigo-400">REORDER</th>
                            <th className="pb-3 text-center">CONFIDENCE</th>
                            <th className="pb-3 text-right">AI INSIGHT</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredPredictions.map((item: any, idx: number) => {
                            const key = `main-${item.product_name}-${idx}`;
                            const isExpanded = !!expandedExplanations[key];
                            return (
                              <React.Fragment key={idx}>
                                <tr className="border-b border-[#1a1b24] hover:bg-[#1a1b24] transition-colors duration-150">
                                  <td className="py-3">
                                    <p className="font-bold text-white text-xs">{item.product_name}</p>
                                    <span className="text-[9px] text-slate-500 font-semibold">{item.date}</span>
                                  </td>
                                  <td className="py-3 text-center text-slate-300 text-xs font-semibold">{item.predicted}</td>
                                  <td className="py-3 text-center font-bold text-white text-xs">{item.actual}</td>
                                  <td className="py-3 text-center font-bold text-indigo-400 text-xs">{item.suggested || "+0"}</td>
                                  <td className="py-3 text-center text-slate-400 text-xs font-semibold">{item.confidence}%</td>
                                  <td className="py-3 text-right">
                                    {item.explanation ? (
                                      <button
                                        onClick={() =>
                                          setExpandedExplanations((prev) => ({
                                            ...prev,
                                            [key]: !prev[key],
                                          }))
                                        }
                                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold transition-all duration-200 ${
                                          isExpanded
                                            ? "bg-indigo-600 text-white shadow-sm shadow-indigo-600/30"
                                            : "bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 hover:bg-indigo-500/30"
                                        }`}
                                      >
                                        <IconSparkles size={12} /> {isExpanded ? "Hide" : "Why?"}
                                      </button>
                                    ) : (
                                      <span className="text-[10px] text-slate-600">--</span>
                                    )}
                                  </td>
                                </tr>
                                 {isExpanded && item.explanation && (
                                   <tr className="bg-indigo-950/20">
                                     <td colSpan={6} className="py-3 px-4">
                                      <div className="bg-[#1c1d27] rounded-2xl p-4 border border-indigo-500/30 shadow-md">
                                        <div className="flex items-start gap-3">
                                          <div className="w-8 h-8 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0 mt-0.5 border border-indigo-500/30">
                                            <IconSparkles size={16} />
                                          </div>
                                          <div>
                                            <div className="flex items-center gap-2 mb-1">
                                              <p className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">AI Prediction Rationale</p>
                                              <span className="text-[9px] bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 px-2 py-0.5 rounded-md font-semibold">Gemini AI</span>
                                            </div>
                                            <p className="text-xs text-slate-300 leading-relaxed font-medium">{item.explanation}</p>
                                          </div>
                                        </div>
                                      </div>
                                    </td>
                                  </tr>
                                )}
                              </React.Fragment>
                            );
                          })}
                          {filteredPredictions.length === 0 && (
                            <tr>
                              <td colSpan={6} className="py-8 text-center text-slate-400 text-xs font-medium">
                                No predictions found.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
                </>
                )}
              </motion.div>
            )}

            {/* VIEW 2: INVENTORY */}
            {activeTab === "inventory" && (
              <motion.div
                key="inventory"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.2 }}
                className="bg-[#13141b] border border-[#1e2029] rounded-3xl p-6 shadow-xl space-y-6"
              >
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-bold text-white text-sm">Product Inventory Catalog</h3>
                    <p className="text-xs text-slate-400">Total catalog: {inventoryList.length} products</p>
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={() => setActiveTab("upload")}
                      className="bg-[#1c1d27] hover:bg-[#252735] text-slate-200 px-4 py-2 border border-[#2e3142] rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all duration-200"
                    >
                      <IconUpload size={16} />
                      Upload CSV Data
                    </button>
                  </div>
                </div>

                {/* Category filters row */}
                <div className="flex gap-2 flex-wrap border-b border-[#1e2029] pb-4">
                  {["All", "Beverages", "Snacks", "Dairy", "Produce", "Household", "Personal Care"].map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setSelectedCategory(cat)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all duration-200 ${
                        selectedCategory === cat
                          ? "bg-white text-slate-950 shadow-md"
                          : "bg-[#1c1d27] text-slate-400 hover:bg-[#252735] hover:text-white"
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>

                {/* Catalog Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="text-[10px] text-slate-400 font-bold border-b border-[#1e2029]">
                        <th className="pb-3 w-[40%]">PRODUCT NAME</th>
                        <th className="pb-3 text-center">CURRENT STOCK</th>
                        <th className="pb-3 text-center">REORDER POINT</th>
                        <th className="pb-3 text-center">STOCK LEVEL</th>
                        <th className="pb-3 text-right">ACTION</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredInventory.map((item: any, idx: number) => {
                        const isLow = item.stock <= item.reorder_point;
                        const isOut = item.stock === 0;
                        return (
                          <tr key={idx} className="border-b border-[#1a1b24] hover:bg-[#1a1b24] transition-colors duration-150">
                            <td className="py-4">
                              <p className="font-bold text-white text-xs">{item.product}</p>
                            </td>
                            <td className="py-4 text-center font-bold text-slate-200 text-xs">{item.stock} units</td>
                            <td className="py-4 text-center text-slate-400 text-xs font-semibold">{item.reorder_point || 0}</td>
                            <td className="py-4 text-center">
                              <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                                isOut 
                                  ? "bg-rose-500/20 text-rose-400 border-rose-500/30" 
                                  : isLow 
                                    ? "bg-amber-500/20 text-amber-400 border-amber-500/30"
                                    : "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                              }`}>
                                {isOut ? "Out of Stock" : isLow ? "Low Stock" : "In Stock"}
                              </span>
                            </td>
                            <td className="py-4 text-right">
                              {restockingProduct === item.product ? (
                                <div className="flex items-center justify-end gap-1.5">
                                  <input
                                    type="number"
                                    value={restockQty}
                                    onChange={(e) => setRestockQty(e.target.value)}
                                    className="w-16 px-1.5 py-0.5 border bg-[#1c1d27] text-white rounded text-center text-xs focus:outline-none focus:border-indigo-500"
                                    onKeyDown={(e) => {
                                      if (e.key === "Enter") {
                                        handleRestock(item.product, parseInt(restockQty, 10) || 50);
                                        setRestockingProduct(null);
                                      } else if (e.key === "Escape") {
                                        setRestockingProduct(null);
                                      }
                                    }}
                                    autoFocus
                                  />
                                  <button
                                    onClick={() => {
                                      handleRestock(item.product, parseInt(restockQty, 10) || 50);
                                      setRestockingProduct(null);
                                    }}
                                    className="bg-indigo-600 hover:bg-indigo-700 text-white px-2.5 py-1 rounded-lg text-[10px] font-bold transition-colors duration-150"
                                  >
                                    Confirm
                                  </button>
                                  <button
                                    onClick={() => setRestockingProduct(null)}
                                    className="text-slate-400 hover:text-slate-200 text-[10px] font-bold px-1.5"
                                  >
                                    Cancel
                                  </button>
                                </div>
                              ) : (
                                <button
                                  onClick={() => {
                                    setRestockingProduct(item.product);
                                    setRestockQty("50");
                                  }}
                                  className="bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-400 px-3 py-1.5 rounded-xl text-[10px] font-bold border border-indigo-500/30 transition-all duration-200"
                                >
                                  Restock
                                </button>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}

            {/* VIEW 3: PREDICTIONS */}
            {activeTab === "predictions" && (
              <motion.div
                key="predictions"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.2 }}
                className="space-y-8"
              >
                {/* Header */}
                <div className="mb-2">
                  <h3 className="font-bold text-white text-sm">Demand Forecasting Engine</h3>
                  <p className="text-xs text-slate-400">AI-powered demand predictions and detailed multi-dimensional inventory rationale</p>
                </div>

                {/* Predictions Logs */}
                <div className="bg-[#13141b] border border-[#1e2029] rounded-3xl p-6 shadow-xl">
                  <h3 className="font-bold text-white text-sm mb-4">Demand Forecast Logs</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="text-[10px] text-slate-400 font-bold border-b border-[#1e2029]">
                          <th className="pb-3 w-[35%]">PRODUCT</th>
                          <th className="pb-3 text-center">DATE</th>
                          <th className="pb-3 text-center">PREDICTED DEMAND</th>
                          <th className="pb-3 text-center">RECOMMENDED ORDER</th>
                          <th className="pb-3 text-center">CONFIDENCE</th>
                          <th className="pb-3 text-right">AI INSIGHT</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredPredictions.map((item: any, idx: number) => (
                          <React.Fragment key={idx}>
                            <tr className="border-b border-[#1a1b24] hover:bg-[#1a1b24] transition-colors duration-150">
                              <td className="py-4">
                                <p className="font-bold text-white text-xs">{item.product_name}</p>
                                <span className="text-[9px] text-slate-500 font-semibold tracking-wider uppercase">{item.sku}</span>
                              </td>
                              <td className="py-4 text-center text-slate-300 text-xs font-semibold">{item.date}</td>
                              <td className="py-4 text-center font-semibold text-slate-200 text-xs">{item.predicted} units</td>
                              <td className="py-4 text-center font-bold text-indigo-400 text-xs">{item.suggested || "+0"}</td>
                              <td className="py-4 text-center">
                                <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                                  item.confidence >= 90 ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' :
                                  item.confidence >= 75 ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' :
                                  'bg-rose-500/20 text-rose-400 border-rose-500/30'
                                }`}>
                                  {item.confidence}%
                                </span>
                              </td>
                              <td className="py-4 text-right">
                                {item.explanation ? (
                                  <button
                                    onClick={() => {
                                      const key = `${item.product_name}-${idx}`;
                                      setExpandedExplanations((prev) => ({
                                        ...prev,
                                        [key]: !prev[key],
                                      }));
                                    }}
                                    className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold transition-all duration-200 ${
                                      expandedExplanations[`${item.product_name}-${idx}`]
                                        ? "bg-indigo-600 text-white shadow-sm shadow-indigo-600/30"
                                        : "bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 hover:bg-indigo-500/30"
                                    }`}
                                  >
                                    <IconSparkles size={12} /> {expandedExplanations[`${item.product_name}-${idx}`] ? "Hide AI" : "Why?"}
                                  </button>
                                ) : (
                                  <span className="text-[10px] text-slate-600">--</span>
                                )}
                              </td>
                            </tr>
                            {expandedExplanations[`${item.product_name}-${idx}`] && item.explanation && (
                              <tr className="bg-indigo-950/20 animate-fadeIn">
                                <td colSpan={6} className="py-3 px-4">
                                  <div className="bg-[#1c1d27] rounded-2xl p-4 border border-indigo-500/30 shadow-md">
                                    <div className="flex items-start gap-3">
                                      <div className="w-8 h-8 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0 mt-0.5 border border-indigo-500/30">
                                        <IconSparkles size={16} />
                                      </div>
                                      <div>
                                        <div className="flex items-center gap-2 mb-1">
                                          <p className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">AI Prediction Rationale</p>
                                          <span className="text-[9px] bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 px-2 py-0.5 rounded-md font-semibold">Gemini AI</span>
                                        </div>
                                        <p className="text-xs text-slate-300 leading-relaxed font-medium">{item.explanation}</p>
                                      </div>
                                    </div>
                                  </div>
                                </td>
                              </tr>
                            )}
                          </React.Fragment>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </motion.div>
            )}

            {/* VIEW 4: AI ASSISTANT CHATBOT */}
            {activeTab === "assistant" && (
              <motion.div
                key="assistant"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.2 }}
                className="flex flex-col h-[calc(100vh-140px)] bg-[#13141b] border border-[#1e2029] rounded-3xl shadow-xl overflow-hidden"
              >
                {/* Assistant Chat Header */}
                <div className="px-6 py-4 border-b border-[#1e2029] flex items-center justify-between bg-[#13141b]">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-indigo-600 text-white flex items-center justify-center font-bold shadow-md shadow-indigo-600/30">
                      <IconSparkles size={20} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-bold text-white text-sm">Stoq AI Assistant</h3>
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> Live Store Context
                        </span>
                      </div>
                      <p className="text-xs text-slate-400">Ask anything about inventory, predictions, reorders, or model diagnostics</p>
                    </div>
                  </div>
                </div>

                {/* Quick Suggestion Chips */}
                <div className="px-6 py-3 border-b border-[#1e2029] bg-[#171822] flex items-center gap-2 overflow-x-auto scrollbar-none">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider shrink-0">Suggestions:</span>
                  {[
                    "What products need reordering today?",
                    "Which products have low stock?",
                    "Show demand forecasts for tomorrow",
                    "Summarize overall model accuracy",
                  ].map((chip, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendChatMessage(chip)}
                      disabled={chatLoading}
                      className="px-3 py-1.5 rounded-full bg-[#1c1d27] hover:bg-indigo-600 hover:text-white border border-[#2e3142] text-slate-300 text-xs font-semibold whitespace-nowrap transition-all duration-200 shrink-0"
                    >
                      {chip}
                    </button>
                  ))}
                </div>

                {/* Messages List */}
                <div className="flex-1 p-6 overflow-y-auto space-y-4 bg-[#0c0d10]/40">
                  <AnimatePresence initial={false}>
                    {chatMessages.map((msg, idx) => (
                      <motion.div
                        key={idx}
                        initial={{ opacity: 0, y: 12, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        transition={{ duration: 0.25, ease: "easeOut" }}
                        className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
                      >
                        <div
                          className={`max-w-2xl px-5 py-3.5 rounded-2xl text-xs leading-relaxed font-medium shadow-md ${
                            msg.sender === "user"
                              ? "bg-indigo-600 text-white rounded-br-none"
                              : "bg-[#1c1d27] text-slate-100 border border-[#2e3142] rounded-bl-none"
                          }`}
                        >
                          <p className="whitespace-pre-wrap">{msg.text}</p>
                        </div>
                        <span className="text-[9px] text-slate-500 mt-1 px-1">{msg.time}</span>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  {chatLoading && (
                    <motion.div
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex items-start gap-2"
                    >
                      <div className="bg-[#1c1d27] border border-[#2e3142] px-4 py-3 rounded-2xl rounded-bl-none shadow-md flex items-center gap-2 text-xs text-slate-300">
                        <IconLoader2 className="animate-spin text-indigo-400" size={16} />
                        <span>Analyzing live store inventory & XGBoost predictions...</span>
                        <div className="flex items-center gap-1 ml-1">
                          <motion.span animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1.2, delay: 0 }} className="w-1.5 h-1.5 rounded-full bg-indigo-500"></motion.span>
                          <motion.span animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1.2, delay: 0.2 }} className="w-1.5 h-1.5 rounded-full bg-indigo-500"></motion.span>
                          <motion.span animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1.2, delay: 0.4 }} className="w-1.5 h-1.5 rounded-full bg-indigo-500"></motion.span>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </div>

                {/* Chat Input Bar */}
                <div className="p-4 bg-[#13141b] border-t border-[#1e2029]">
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleSendChatMessage();
                    }}
                    className="flex items-center gap-2"
                  >
                    <input
                      type="text"
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      placeholder="Ask Stoq Assistant about inventory, reorders, demand forecasts..."
                      disabled={chatLoading}
                      className="flex-1 bg-[#1c1d27] border rounded-2xl px-4 py-3 text-xs text-white focus:outline-none focus:border-indigo-500 transition-all duration-200 font-medium"
                    />
                    <button
                      type="submit"
                      disabled={!chatInput.trim() || chatLoading}
                      className="hover:bg-indigo-700 disabled:bg-indigo-900 text-white px-5 py-3 rounded-2xl text-xs font-bold transition-all duration-200 flex items-center gap-1.5 shadow-md shadow-indigo-600/30 shrink-0"
                    >
                      <span>Send</span>
                      <IconSend size={14} />
                    </button>
                  </form>
                </div>
              </motion.div>
            )}

            {/* VIEW 5: UPLOAD */}
            {activeTab === "upload" && (
              <motion.div
                key="upload"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.2 }}
                className="bg-[#13141b] border border-[#1e2029] rounded-3xl p-8 shadow-xl max-w-2xl mx-auto space-y-6"
              >
                <div className="flex items-start justify-between gap-4 border-b border-[#1e2029] pb-4">
                  <div>
                    <h3 className="font-bold text-white text-sm">Upload Sales CSV Data</h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Upload your daily sales history in CSV format. The AI agent will ingest data, build features, retrain models, and regenerate forecasts dynamically.
                    </p>
                  </div>
                  <a
                    href="/sample_retail_sales.csv"
                    download="sample_retail_sales.csv"
                    className="bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-400 border border-indigo-500/30 px-3.5 py-2 rounded-xl text-xs font-bold transition-all duration-200 flex items-center gap-1.5 shrink-0 shadow-sm"
                  >
                    <IconUpload size={14} className="rotate-180 text-indigo-400" />
                    <span>Sample CSV</span>
                  </a>
                </div>

                <div className="border-2 border-dashed border-[#2e3142] rounded-2xl p-8 text-center flex flex-col items-center justify-center gap-3">
                  <IconUpload size={40} className="text-slate-400" />
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-slate-200">Choose CSV file here</p>
                    <p className="text-[10px] text-slate-400">Required headers: product_name, sku, category, sale_date, quantity_sold, price, current_stock, reorder_point</p>
                  </div>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    className="hidden"
                    id="csv-file-input"
                  />
                  <label
                    htmlFor="csv-file-input"
                    className="mt-2 inline-block bg-[#1c1d27] hover:bg-[#252735] text-slate-200 px-4 py-2 rounded-xl text-xs font-bold cursor-pointer select-none transition-all duration-200 border border-[#2e3142]"
                  >
                    Select CSV File
                  </label>
                  {file && (
                    <p className="text-xs font-semibold text-indigo-400 mt-1">
                      Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
                    </p>
                  )}
                </div>

                <button
                  onClick={handleUploadCSV}
                  disabled={!file || uploadLoading}
                  className="w-full hover:bg-indigo-700 disabled:bg-indigo-900 text-white py-3 rounded-xl text-xs font-bold transition-all duration-200 flex items-center justify-center gap-2 select-none shadow-md shadow-indigo-600/30"
                >
                  {uploadLoading ? (
                    <>
                      <IconLoader2 className="animate-spin" size={16} />
                      Ingesting & Retraining Models...
                    </>
                  ) : (
                    "Upload and Forecast Sales"
                  )}
                </button>

                {uploadMessage && (
                  <div className={`p-4 rounded-xl text-xs font-semibold ${
                    uploadSuccess 
                      ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" 
                      : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                  }`}>
                    {uploadMessage}
                  </div>
                )}
              </motion.div>
            )}

          </AnimatePresence>
        </main>
      </div>

    </div>
  );
}