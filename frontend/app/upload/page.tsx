"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { uploadFile } from "@/services/api";
import { useAppStore } from "@/store/appStore";
import { Upload, AlertCircle, CheckCircle, Loader } from "lucide-react";
import Link from "next/link";

export default function UploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const setJobId = useAppStore((state) => state.setJobId);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.name.endsWith(".step") || file.type.includes("step")) {
        setSelectedFile(file);
        setError(null);
      } else {
        setError("Proszę wybrać plik .step");
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (files && files.length > 0) {
      setSelectedFile(files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);

    try {
      const response = await uploadFile(selectedFile);
      setSuccess(true);

      // Store the job ID and model ID in app store
      setJobId(response.job_id, response.model_id);

      // Redirect to progress page with model ID as query param
      const modelIdParam = new URLSearchParams({
        modelId: response.model_id,
      }).toString();

      setTimeout(() => {
        router.push(`/progress/${response.job_id}?${modelIdParam}`);
      }, 500);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Błąd przy przesyłaniu pliku";
      setError(errorMessage);
      setLoading(false);
    }
  };

  return (
    <main className="flex-1 flex items-center justify-center min-h-screen px-4 py-8 bg-gradient-to-br from-black-500 via-black-400 to-black-600">
      <div className="w-full max-w-2xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-gold-300">
            Prześlij plik STEP
          </h1>
          <p className="text-gold-100">
            Przeciągnij i upuść plik lub kliknij aby wybrać
          </p>
        </div>

        {/* Upload Card */}
        <Card className="rounded-3xl p-12 bg-black-600 border border-gold-600">
          <div
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            className="text-center space-y-6"
          >
            {/* Upload Icon */}
            <div className="flex justify-center">
              <div className="p-4 bg-gold-500 rounded-3xl">
                <Upload className="w-12 h-12 text-black-500" />
              </div>
            </div>

            {/* Upload Text */}
            <div className="space-y-2">
              <p className="text-lg font-semibold text-gold-300">
                Przeciągnij plik tutaj lub kliknij aby wybrać
              </p>
              <p className="text-sm text-gold-100">
                Akceptowane pliki: .step
              </p>
            </div>

            {/* Hidden File Input */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".step"
              onChange={handleFileSelect}
              className="hidden"
            />

            {/* Upload Button */}
            <Button
              onClick={() => fileInputRef.current?.click()}
              variant="outline"
              className="px-6 py-2 rounded-3xl border-gold-500 text-gold-300 bg-black-600 hover:bg-gold-500 hover:text-black-500 hover:border-gold-600 transition-colors"
            >
              Wybierz plik
            </Button>
          </div>
        </Card>

        {/* Selected File Display */}
        {selectedFile && !success && (
          <Card className="rounded-3xl p-6 bg-black-600 border-gold-600">
            <div className="flex items-center gap-4">
              <CheckCircle className="w-6 h-6 text-gold-500 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-gold-300 truncate">
                  {selectedFile.name}
                </p>
                <p className="text-sm text-gold-100">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
          </Card>
        )}

        {/* Error Alert */}
        {error && (
          <Alert className="border-red-600 bg-red-950 rounded-3xl">
            <AlertCircle className="h-4 w-4 text-red-400" />
            <AlertDescription className="text-red-300">
              {error}
            </AlertDescription>
          </Alert>
        )}

        {/* Success Alert */}
        {success && (
          <Alert className="border-gold-600 bg-black-600 rounded-3xl">
            <CheckCircle className="h-4 w-4 text-gold-400" />
            <AlertDescription className="text-gold-300">
              Plik przesłany pomyślnie! Przekierowuję...
            </AlertDescription>
          </Alert>
        )}

        {/* Action Buttons */}
        <div className="flex gap-4 justify-center pt-4">
          <Link href="/">
            <Button
              variant="outline"
              className="px-8 py-6 rounded-3xl border-gold-500 text-gold-300 hover:bg-gold-500 hover:text-black-500 transition-colors"
            >
              ← Powrót
            </Button>
          </Link>

          <Button
            onClick={handleUpload}
            disabled={!selectedFile || loading}
            className="px-8 py-6 bg-gold-500 hover:bg-gold-600 text-black-500 font-semibold rounded-3xl disabled:opacity-50 disabled:bg-gold-300 transition-colors"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <Loader className="w-4 h-4 animate-spin" />
                Przesyłanie...
              </span>
            ) : (
              "Przesłij"
            )}
          </Button>
        </div>
      </div>
    </main>
  );
}
