import { useState, useCallback } from "react";
import { Upload, FileCode, Image, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function DropZone({ onFileUpload, loading, error }) {
  const [isDragging, setIsDragging] = useState(false);
  const [fileName, setFileName] = useState(null);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragOut = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      const files = e.dataTransfer?.files;
      if (files && files.length > 0) {
        setFileName(files[0].name);
        onFileUpload(files[0]);
      }
    },
    [onFileUpload],
  );

  const handleFileInput = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      onFileUpload(file);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center mt-8">
      {/* Title */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-10"
      >
        <h2 className="text-2xl md:text-3xl font-bold text-gray-700 mb-3">
          코드나 스크린샷을 올려보세요
        </h2>
        <p className="text-gray-400 text-sm md:text-base max-w-lg mx-auto">
          수업에서 다루는 파일(.py, .html 등)이나 코드 캡처 이미지를 올리면,
          <br className="hidden sm:block" />
          AI가 커리큘럼 상의 현재 위치를 알려드립니다.
        </p>
      </motion.div>

      {/* Drop Area */}
      <AnimatePresence mode="wait">
        {loading ? (
          <motion.div
            key="loading"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="flex flex-col items-center justify-center w-full max-w-xl h-72 rounded-3xl bg-white border-2 border-indigo-200 shadow-lg"
          >
            <Loader2 size={40} className="text-indigo-400 animate-spin mb-4" />
            <p className="text-indigo-500 font-semibold text-lg">
              AI가 학습 맥락을 분석 중입니다...
            </p>
            {fileName && (
              <p className="text-gray-400 text-sm mt-2">{fileName}</p>
            )}
            <div className="mt-4 flex gap-1">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  className="w-2 h-2 rounded-full bg-indigo-300"
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{
                    duration: 1.2,
                    repeat: Infinity,
                    delay: i * 0.2,
                  }}
                />
              ))}
            </div>
          </motion.div>
        ) : (
          <motion.label
            key="dropzone"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            htmlFor="file-input"
            className={`
              relative flex flex-col items-center justify-center cursor-pointer
              w-full max-w-xl h-72 rounded-3xl border-2 border-dashed
              transition-all duration-300 ease-out
              ${
                isDragging
                  ? "border-indigo-400 bg-indigo-50 shadow-xl shadow-indigo-100 scale-[1.02]"
                  : "border-gray-200 bg-white hover:border-indigo-300 hover:bg-indigo-50/40 shadow-lg hover:shadow-xl"
              }
            `}
            onDragEnter={handleDragIn}
            onDragLeave={handleDragOut}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              id="file-input"
              type="file"
              className="hidden"
              onChange={handleFileInput}
              accept=".py,.html,.css,.js,.jsx,.ts,.tsx,.java,.c,.cpp,.json,.sql,.txt,.ipynb,.png,.jpg,.jpeg,.gif,.webp,.bmp"
            />

            <div
              className={`
                flex items-center justify-center w-16 h-16 rounded-2xl mb-5 transition-colors
                ${isDragging ? "bg-indigo-200" : "bg-indigo-100"}
              `}
            >
              <Upload
                size={28}
                className={`transition-colors ${isDragging ? "text-indigo-600" : "text-indigo-400"}`}
              />
            </div>

            <p className="text-gray-600 font-medium text-base mb-1">
              {isDragging
                ? "여기에 놓으세요!"
                : "파일을 드래그하거나 클릭하세요"}
            </p>
            <p className="text-gray-300 text-xs">
              코드 파일(.py .html .js 등) 또는 이미지(.png .jpg)
            </p>

            {/* File type badges */}
            <div className="flex gap-2 mt-5">
              <span className="flex items-center gap-1 px-3 py-1 bg-blue-50 text-blue-400 rounded-full text-xs font-medium">
                <FileCode size={12} /> 코드 파일
              </span>
              <span className="flex items-center gap-1 px-3 py-1 bg-purple-50 text-purple-400 rounded-full text-xs font-medium">
                <Image size={12} /> 스크린샷
              </span>
            </div>
          </motion.label>
        )}
      </AnimatePresence>

      {/* Error message */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 px-5 py-3 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm max-w-xl w-full text-center"
        >
          {error}
        </motion.div>
      )}
    </div>
  );
}
