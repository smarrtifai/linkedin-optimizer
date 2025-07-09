import React, { useRef, useState } from "react";
import axios from "axios";
import html2pdf from "html2pdf.js";
import {
  FaLinkedin,
  FaFilePdf,
  FaSearch,
  FaFileUpload,
  FaUserTie,
  FaBriefcase,
  FaTools,
  FaCheckCircle,
} from "react-icons/fa";
import { PieChart, Pie, Cell, Label } from "recharts";
import "./index.css";

function App() {
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const pieChartRef = useRef(null);

  const sectionIcons = {
    about: <FaUserTie className="text-orange-500 mr-2" />,
    experience: <FaBriefcase className="text-orange-500 mr-2" />,
    skills: <FaTools className="text-orange-500 mr-2" />,
    completeness: <FaCheckCircle className="text-orange-500 mr-2" />,
  };

  const handleFileChange = (e) => {
    const uploadedFile = e.target.files[0];
    setFile(uploadedFile);
    setFileName(uploadedFile?.name || "");
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    setFile(droppedFile);
    setFileName(droppedFile?.name || "");
  };

  const handleAnalyze = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append("pdf", file);
    setLoading(true);
    try {
      const response = await axios.post(`${process.env.REACT_APP_API_BASE}/upload`, formData);
      setData(response.data.suggestions);
      setTimeout(() => {
        pieChartRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 600);
    } catch (err) {
      alert("❌ Error analyzing. Try again.");
    }
    setLoading(false);
  };

  const handleExport = () => {
    const element = document.getElementById("report-content");
    if (!element) return;

    // Save original styles
    const originalStyles = {
      backgroundColor: element.style.backgroundColor,
      color: element.style.color,
    };

    // Flatten Tailwind styles for export
    element.style.backgroundColor = "#ffffff";
    element.style.color = "#000000";

    // Inline styles for all children
    const allChildren = element.querySelectorAll("*");
    const originalChildStyles = [];

    allChildren.forEach((child, i) => {
      originalChildStyles[i] = {
        color: child.style.color,
        backgroundColor: child.style.backgroundColor,
        boxShadow: child.style.boxShadow,
        backgroundImage: child.style.backgroundImage,
        filter: child.style.filter,
      };

      child.style.color = "#000000";
      child.style.backgroundColor = "transparent";
      child.style.boxShadow = "none";
      child.style.backgroundImage = "none";
      child.style.filter = "none";
    });

    // Export as high-quality PDF
    html2pdf()
      .set({
        margin: 0.5,
        filename: "linkedin_report.pdf",
        image: { type: "jpeg", quality: 1 },
        html2canvas: {
          scale: 3,
          useCORS: true,
          backgroundColor: "#ffffff",
        },
        jsPDF: {
          unit: "in",
          format: "letter",
          orientation: "portrait",
        },
      })
      .from(element)
      .save()
      .finally(() => {
        // Restore original styles
        element.style.backgroundColor = originalStyles.backgroundColor;
        element.style.color = originalStyles.color;
        allChildren.forEach((child, i) => {
          child.style.color = originalChildStyles[i].color;
          child.style.backgroundColor = originalChildStyles[i].backgroundColor;
          child.style.boxShadow = originalChildStyles[i].boxShadow;
          child.style.backgroundImage = originalChildStyles[i].backgroundImage;
          child.style.filter = originalChildStyles[i].filter;
        });
      });
  };



  const getGradientByScore = (score) => {
    if (score <= 40) return ["#f44336", "#ff5722"];
    if (score <= 75) return ["#ff9800", "#ffc107"];
    return ["#4caf50", "#8bc34a"];
  };

  const parseContent = (section) => {
    return (section || "")
      .split("\n")
      .filter((line) => line.trim())
      .map((line, index) => {
        const lower = line.toLowerCase();
        if (lower.startsWith("score"))
          return <p key={index} className="font-bold text-md text-orange-600">{line}</p>;
        if (lower.startsWith("insight"))
          return <p key={index} className="font-semibold text-gray-800 mt-3">{line}</p>;
        if (lower.startsWith("suggestions"))
          return <p key={index} className="font-semibold text-orange-500 mt-2 mb-1">{line}</p>;
        if (lower.startsWith("suggestion"))
          return <li key={index} className="list-disc ml-6 text-gray-700">{line.replace(/^suggestion\s*\d*:?/i, '')}</li>;
        return <p key={index} className="text-gray-600">{line}</p>;
      });
  };

  const pieData = data?.overallscore
    ? [
        { name: "Score", value: data.overallscore },
        { name: "Remaining", value: 100 - data.overallscore },
      ]
    : [];

  const [startColor, endColor] = getGradientByScore(data?.overallscore || 0);

  return (
    <div className="min-h-screen bg-orange-50 text-gray-800 font-poppins">
      <div className="max-w-7xl mx-auto px-6 py-10 relative">
        {/* Header */}
        <div className="bg-orange-100 rounded-lg shadow-md p-6 mb-10">
          <div className="flex flex-col sm:flex-row items-center sm:justify-between gap-4">
            <div className="flex-shrink-0">
              <img
                src="/logo.png"
                alt="Logo"
                className="h-20 sm:h-24 cursor-pointer"
                onClick={() => (window.location.href = 'https://www.smarrtifai.com')}
              />
            </div>

            <div className="text-center sm:text-left">
              <div className="flex items-center justify-center sm:justify-start gap-2 mb-1">
                <FaLinkedin className="text-4xl text-orange-600" />
                <h1 className="text-3xl sm:text-5xl font-extrabold bg-gradient-to-r from-orange-500 via-red-500 to-yellow-500 text-transparent bg-clip-text">
                  LinkedIn Optimizer
                </h1>
              </div>
              <p className="text-sm sm:text-base text-gray-700 italic">
                Get instant, AI-powered feedback on your profile
              </p>
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="bg-white p-8 rounded-lg shadow-md border-l-4 border-orange-500 mb-12">
          <h2 className="text-3xl font-bold text-orange-600 mb-8 text-center">
            📥 How to Download Your LinkedIn Profile as PDF
          </h2>
          <div className="grid md:grid-cols-2 gap-10 mb-10">
            <div className="text-center space-y-4">
              <p className="text-lg font-semibold text-orange-700">
                1. Open your LinkedIn profile and click on the <strong>“More”</strong> button.
              </p>
              <img src="/images/step1.png" alt="Step 1" className="rounded shadow border w-full max-w-lg mx-auto" />
            </div>
            <div className="text-center space-y-4">
              <p className="text-lg font-semibold text-orange-700">
                2. Select <strong>“Save to PDF”</strong> from the dropdown.
              </p>
              <img src="/images/step2.png" alt="Step 2" className="rounded shadow border w-full max-w-lg mx-auto" />
            </div>
          </div>
          <div className="text-center space-y-4">
            <p className="text-lg font-semibold text-orange-700">
              3. Your profile will be downloaded automatically as a PDF.
            </p>
            <img src="/images/step3.png" alt="Step 3" className="rounded shadow border w-full max-w-md mx-auto" />
          </div>
        </div>

        {/* Upload Section */}
        <div
          className={`bg-white p-6 rounded-lg shadow-md mb-10 border-2 ${
            isDragging ? "border-orange-500" : "border-dashed border-orange-300"
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
        >
          <label className="flex flex-col items-center gap-2 cursor-pointer">
            <FaFileUpload className="text-3xl text-orange-600" />
            <span className="text-orange-700 font-medium">
              {fileName || "Drag & Drop or Click to Upload LinkedIn PDF"}
            </span>
            <input type="file" accept=".pdf" onChange={handleFileChange} className="hidden" />
          </label>

          <div className="flex flex-wrap gap-4 justify-center mt-6">
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="bg-red-500 hover:bg-red-600 text-white px-5 py-2 rounded font-semibold transition flex items-center gap-2"
            >
              <FaSearch />
              {loading ? "Analyzing..." : "Analyze PDF"}
            </button>

            <button
              onClick={handleExport}
              className="bg-orange-500 hover:bg-orange-600 text-white px-5 py-2 rounded font-semibold transition flex items-center gap-2"
            >
              <FaFilePdf />
              Export as PDF
            </button>
          </div>
        </div>

        {/* Report */}
        {data && (
          <div id="report-content" className="space-y-10 mt-12 bg-white p-6 rounded-lg animate-fade-in">
            <div ref={pieChartRef} className="flex flex-col items-center justify-center text-center">
              <p className="font-semibold text-xl mb-2">
                Overall Profile Score: {data.overallscore}/100
              </p>
              <PieChart width={200} height={200}>
                <defs>
                  <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor={startColor} />
                    <stop offset="100%" stopColor={endColor} />
                  </linearGradient>
                </defs>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  startAngle={90}
                  endAngle={-270}
                  dataKey="value"
                  isAnimationActive
                >
                  <Cell key="score" fill="url(#scoreGradient)" />
                  <Cell key="remaining" fill="#e0e0e0" />
                  <Label
                    value={`${data.overallscore}%`}
                    position="center"
                    fill="#111"
                    style={{ fontSize: "20px", fontWeight: "bold" }}
                  />
                </Pie>
              </PieChart>
            </div>

            {["about", "experience", "skills", "completeness"].map((key) => (
              <div key={key} className="bg-white p-6 rounded-lg shadow-md border-l-4 border-orange-400 transition transform hover:scale-[1.01]">
                <h2 className="flex items-center text-2xl text-orange-600 font-semibold capitalize mb-2 border-b pb-1">
                  {sectionIcons[key]} {key}
                </h2>
                <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                  <div
                    className="bg-orange-500 h-2 rounded-full"
                    style={{ width: `${Math.min(100, data.overallscore || 0)}%` }}
                  />
                </div>
                {data[key] ? (
                  <ul className="space-y-2">{parseContent(data[key])}</ul>
                ) : (
                  <p className="italic text-sm text-gray-500">No content available for this section.</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
