"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Step = "measure" | "garment" | "tryon" | "result";

type SizeResult = {
    recommended_size: string;
    confidence_pct: number;
    fit_notes: string;
    alternate_size: string;
    return_risk: string;
};

type TryOnResult = {
    result_url: string | null;
    status: string;
};

export default function TwinFitApp() {
    const [step, setStep] = useState<Step>("measure");
    const [loading, setLoading] = useState(false);

    // Measurements form
    const [measurements, setMeasurements] = useState({
        height_cm: "", weight_kg: "",
        chest_cm: "", waist_cm: "", hip_cm: "",
        brand: "myntra", category: "kurta",
    });

    const [sizeResult, setSizeResult] = useState<SizeResult | null>(null);

    // Garment
    const [garmentUrl, setGarmentUrl] = useState("");
    const [garmentMeta, setGarmentMeta] = useState<any>(null);

    // Try-on
    const [userPhoto, setUserPhoto] = useState<string | null>(null);
    const [tryOnResult, setTryOnResult] = useState<TryOnResult | null>(null);
    const [jobId, setJobId] = useState<string | null>(null);

    // ─── Handlers ─────────────────────────────────────────────────────────

    async function handleSizeRecommend() {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/api/size/recommend`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    ...Object.fromEntries(
                        Object.entries(measurements).map(([k, v]) =>
                            ["height_cm", "weight_kg", "chest_cm", "waist_cm", "hip_cm"].includes(k)
                                ? [k, parseFloat(v as string)]
                                : [k, v]
                        )
                    ),
                }),
            });
            if (!res.ok) {
                const err = await res.json().catch(() => null);
                alert("Size recommendation failed: " + (err?.detail?.[0]?.msg || err?.detail || res.statusText));
                setLoading(false);
                return;
            }
            const data = await res.json();
            setSizeResult(data);
            setStep("garment");
        } catch (e) {
            alert("Size recommendation failed. Is the backend running?");
        }
        setLoading(false);
    }

    async function handleGarmentAnalyze() {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/api/garment/analyze`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ image_url: garmentUrl }),
            });
            const data = await res.json();
            setGarmentMeta(data);
            setStep("tryon");
        } catch (e) {
            alert("Garment analysis failed.");
        }
        setLoading(false);
    }

    function handlePhotoUpload(e: React.ChangeEvent<HTMLInputElement>) {
        const file = e.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => {
            // Strip the data:image/jpeg;base64, prefix — backend wants raw base64
            const b64 = (reader.result as string).split(",")[1];
            setUserPhoto(b64);
        };
        reader.readAsDataURL(file);
    }

    async function handleStartTryOn() {
        if (!userPhoto) return alert("Please upload your photo first.");
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/api/tryon/start`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    user_photo_b64: userPhoto,
                    garment_image_url: garmentUrl,
                    garment_category: garmentMeta?.category || "top",
                }),
            });
            const data = await res.json();
            setJobId(data.job_id);
            pollTryOn(data.job_id);
        } catch (e) {
            alert("Try-on failed to start.");
            setLoading(false);
        }
    }

    async function pollTryOn(id: string) {
        const interval = setInterval(async () => {
            const res = await fetch(`${API_BASE}/api/tryon/status/${id}`);
            const data = await res.json();
            if (data.status === "done") {
                setTryOnResult(data);
                setStep("result");
                setLoading(false);
                clearInterval(interval);
            } else if (data.status === "failed") {
                alert("Try-on failed: " + data.error);
                setLoading(false);
                clearInterval(interval);
            }
        }, 3000);
    }

    // ─── UI ───────────────────────────────────────────────────────────────

    const riskColor: Record<string, string> = {
        LOW: "text-green-600", MEDIUM: "text-yellow-600", HIGH: "text-red-600"
    };

    return (
        <div className="min-h-screen bg-gray-50 font-sans">
            {/* Header */}
            <header className="bg-[#1E3A5F] text-white px-6 py-4 flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">TwinFit</h1>
                    <p className="text-blue-200 text-xs">AI Virtual Try-On · India's Fit Problem, Solved</p>
                </div>
                <span className="text-xs bg-blue-800 px-3 py-1 rounded-full">
                    AMD Developer Hackathon
                </span>
            </header>

            {/* Progress bar */}
            <div className="bg-white border-b px-6 py-3 flex gap-4 text-sm">
                {(["measure", "garment", "tryon", "result"] as Step[]).map((s, i) => (
                    <div key={s} className={`flex items-center gap-2 ${step === s ? "text-blue-700 font-semibold" : "text-gray-400"}`}>
                        <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs
              ${step === s ? "bg-[#1E3A5F] text-white" : "bg-gray-200"}`}>
                            {i + 1}
                        </span>
                        {s.charAt(0).toUpperCase() + s.slice(1)}
                    </div>
                ))}
            </div>

            <main className="max-w-2xl mx-auto p-6 space-y-6">

                {/* ── Step 1: Measurements ── */}
                {step === "measure" && (
                    <div className="bg-white rounded-xl shadow p-6 space-y-4">
                        <h2 className="text-xl font-bold text-[#1E3A5F]">Your Measurements</h2>
                        <p className="text-sm text-gray-500">Enter your measurements in cm to get your perfect size.</p>

                        <div className="grid grid-cols-2 gap-4">
                            {[
                                ["Height (cm)", "height_cm", "165"],
                                ["Weight (kg)", "weight_kg", "60"],
                                ["Chest (cm)", "chest_cm", "88"],
                                ["Waist (cm)", "waist_cm", "72"],
                                ["Hip (cm)", "hip_cm", "96"],
                            ].map(([label, key, placeholder]) => (
                                <div key={key}>
                                    <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
                                    <input
                                        type="number"
                                        placeholder={placeholder}
                                        value={measurements[key as keyof typeof measurements]}
                                        onChange={e => setMeasurements(p => ({ ...p, [key]: e.target.value }))}
                                        className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                                    />
                                </div>
                            ))}

                            <div>
                                <label className="block text-xs font-medium text-gray-600 mb-1">Brand</label>
                                <select
                                    value={measurements.brand}
                                    onChange={e => setMeasurements(p => ({ ...p, brand: e.target.value }))}
                                    className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                                >
                                    <option value="myntra">Myntra</option>
                                    <option value="h&m">H&M</option>
                                    <option value="zara">Zara</option>
                                    <option value="generic">Generic</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-xs font-medium text-gray-600 mb-1">Category</label>
                                <select
                                    value={measurements.category}
                                    onChange={e => setMeasurements(p => ({ ...p, category: e.target.value }))}
                                    className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                                >
                                    <option value="kurta">Kurta</option>
                                    <option value="top">Top</option>
                                    <option value="dress">Dress</option>
                                    <option value="jeans">Jeans</option>
                                    <option value="jacket">Jacket</option>
                                </select>
                            </div>
                        </div>

                        <button
                            onClick={handleSizeRecommend}
                            disabled={loading}
                            className="w-full bg-[#1E3A5F] text-white py-3 rounded-lg font-semibold hover:bg-blue-900 transition disabled:opacity-50"
                        >
                            {loading ? "Analyzing…" : "Get My Size →"}
                        </button>
                    </div>
                )}

                {/* ── Step 2: Garment ── */}
                {step === "garment" && sizeResult && (
                    <div className="space-y-4">
                        {/* Size result card */}
                        <div className="bg-white rounded-xl shadow p-6">
                            <h2 className="text-xl font-bold text-[#1E3A5F] mb-1">Your Recommended Size</h2>
                            <div className="flex items-end gap-4 my-3">
                                <span className="text-6xl font-black text-[#1E3A5F]">{sizeResult.recommended_size}</span>
                                <div>
                                    <p className="text-sm text-gray-500">Confidence</p>
                                    <p className="text-2xl font-bold text-green-600">{sizeResult.confidence_pct}%</p>
                                </div>
                                <div className="ml-auto text-right">
                                    <p className="text-xs text-gray-400">Return Risk</p>
                                    <p className={`font-bold ${riskColor[sizeResult.return_risk]}`}>{sizeResult.return_risk}</p>
                                </div>
                            </div>
                            <p className="text-sm text-gray-600 bg-blue-50 rounded-lg p-3">{sizeResult.fit_notes}</p>
                            {sizeResult.alternate_size && (
                                <p className="text-xs text-gray-400 mt-2">
                                    Between sizes? Also try <strong>{sizeResult.alternate_size}</strong>
                                </p>
                            )}
                        </div>

                        {/* Garment URL input */}
                        <div className="bg-white rounded-xl shadow p-6 space-y-4">
                            <h2 className="text-xl font-bold text-[#1E3A5F]">Paste Garment Image URL</h2>
                            <p className="text-sm text-gray-500">
                                Paste any Myntra/AJIO/Zara product image URL. Gemma AI will analyze it.
                            </p>
                            <input
                                type="url"
                                placeholder="https://assets.myntra.com/..."
                                value={garmentUrl}
                                onChange={e => setGarmentUrl(e.target.value)}
                                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                            />
                            <button
                                onClick={handleGarmentAnalyze}
                                disabled={loading || !garmentUrl}
                                className="w-full bg-[#1E3A5F] text-white py-3 rounded-lg font-semibold hover:bg-blue-900 transition disabled:opacity-50"
                            >
                                {loading ? "Analyzing garment with Gemma AI…" : "Analyze Garment →"}
                            </button>
                        </div>
                    </div>
                )}

                {/* ── Step 3: Try-On ── */}
                {step === "tryon" && garmentMeta && (
                    <div className="space-y-4">
                        {/* Garment metadata card */}
                        <div className="bg-white rounded-xl shadow p-6">
                            <h2 className="text-lg font-bold text-[#1E3A5F] mb-3">Garment Analyzed ✓</h2>
                            <div className="grid grid-cols-3 gap-3">
                                {[
                                    ["Category", garmentMeta.category],
                                    ["Sleeve", garmentMeta.sleeve_type],
                                    ["Fit", garmentMeta.fit_type],
                                    ["Fabric", garmentMeta.fabric_est],
                                    ["Color", garmentMeta.color],
                                    ["For", garmentMeta.gender_target],
                                ].map(([k, v]) => (
                                    <div key={k} className="bg-gray-50 rounded-lg p-2 text-center">
                                        <p className="text-xs text-gray-400">{k}</p>
                                        <p className="text-sm font-semibold text-gray-700 capitalize">{v}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Photo upload */}
                        <div className="bg-white rounded-xl shadow p-6 space-y-4">
                            <h2 className="text-xl font-bold text-[#1E3A5F]">Upload Your Photo</h2>
                            <p className="text-sm text-gray-500">
                                Stand straight, full body visible. Front-facing photo works best.
                            </p>
                            <label className="flex flex-col items-center justify-center border-2 border-dashed border-blue-300 rounded-xl p-8 cursor-pointer hover:bg-blue-50 transition">
                                <span className="text-3xl mb-2">📸</span>
                                <span className="text-sm text-blue-600 font-medium">Click to upload photo</span>
                                <span className="text-xs text-gray-400 mt-1">JPG, PNG up to 10MB</span>
                                <input type="file" accept="image/*" onChange={handlePhotoUpload} className="hidden" />
                            </label>
                            {userPhoto && (
                                <p className="text-xs text-green-600 text-center">✓ Photo uploaded successfully</p>
                            )}
                            <button
                                onClick={handleStartTryOn}
                                disabled={loading || !userPhoto}
                                className="w-full bg-[#1E3A5F] text-white py-3 rounded-lg font-semibold hover:bg-blue-900 transition disabled:opacity-50"
                            >
                                {loading ? "Generating try-on… (takes 15–30s)" : "See How It Looks →"}
                            </button>
                        </div>
                    </div>
                )}

                {/* ── Step 4: Result ── */}
                {step === "result" && tryOnResult && (
                    <div className="bg-white rounded-xl shadow p-6 space-y-4">
                        <h2 className="text-xl font-bold text-[#1E3A5F]">Your Virtual Try-On</h2>
                        {tryOnResult.result_url ? (
                            <img
                                src={tryOnResult.result_url}
                                alt="Virtual try-on result"
                                className="w-full rounded-xl object-cover max-h-[600px]"
                            />
                        ) : (
                            <div className="bg-gray-100 rounded-xl h-64 flex items-center justify-center">
                                <p className="text-gray-400">Result loading…</p>
                            </div>
                        )}

                        {/* Summary */}
                        <div className="grid grid-cols-2 gap-3">
                            <div className="bg-green-50 rounded-lg p-3 text-center">
                                <p className="text-xs text-gray-500">Recommended Size</p>
                                <p className="text-2xl font-black text-green-700">{sizeResult?.recommended_size}</p>
                            </div>
                            <div className="bg-blue-50 rounded-lg p-3 text-center">
                                <p className="text-xs text-gray-500">Confidence</p>
                                <p className="text-2xl font-black text-blue-700">{sizeResult?.confidence_pct}%</p>
                            </div>
                        </div>

                        <button
                            onClick={() => { setStep("measure"); setSizeResult(null); setTryOnResult(null); }}
                            className="w-full border border-[#1E3A5F] text-[#1E3A5F] py-3 rounded-lg font-semibold hover:bg-blue-50 transition"
                        >
                            Try Another Outfit
                        </button>
                    </div>
                )}

                {/* Footer stat */}
                <div className="text-center text-xs text-gray-400 pb-4">
                    Indian fashion returns: 25–35% · TwinFit targets a 20% reduction
                    <br />Powered by Gemma 3 on AMD GPU · Built for AMD Developer Hackathon ACT II
                </div>
            </main>
        </div>
    );
}
