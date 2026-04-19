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
    <main className="flex-1 flex items-center justify-center min-h-screen px-4 py-8">
      <div className="w-full max-w-2xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-black-DEFAULT">
            Prześlij plik STEP
          </h1>
          <p className="text-charcoal-500">
            Przeciągnij i upuść plik lub kliknij aby wybrać
          </p>
        </div>

        {/* Upload Card */}
        <Card className="rounded-3xl p-12 bg-lilac_ash-300 border border-lilac_ash-500">
          <div
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            className="text-center space-y-6"
          >
            {/* Upload Icon */}
            <div className="flex justify-center">
              <div className="p-4 bg-lilac_ash-500 rounded-3xl">
                <Upload className="w-12 h-12 text-bright_snow-800" />
              </div>
            </div>

            {/* Upload Text */}
            <div className="space-y-2">
              <p className="text-lg font-semibold text-charcoal-800">
                Przeciągnij plik tutaj lub kliknij aby wybrać
              </p>
              <p className="text-sm text-charcoal-700">
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
              className="px-6 py-2 rounded-3xl border-lilac_ash-600 text-charcoal-700 bg-lilac_ash-200 hover:bg-lilac_ash-400 hover:border-lilac_ash-700 transition-colors"
            >
              Wybierz plik
            </Button>
          </div>
        </Card>

        {/* Selected File Display */}
        {selectedFile && !success && (
          <Card className="rounded-3xl p-6 bg-lilac_ash-200 border-lilac_ash-500">
            <div className="flex items-center gap-4">
              <CheckCircle className="w-6 h-6 text-lilac_ash-600 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-charcoal-800 truncate">
                  {selectedFile.name}
                </p>
                <p className="text-sm text-charcoal-700">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
          </Card>
        )}

        {/* Error Alert */}
        {error && (
          <Alert className="border-red-200 bg-red-50 rounded-3xl">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              {error}
            </AlertDescription>
          </Alert>
        )}

        {/* Success Alert */}
        {success && (
          <Alert className="border-lilac_ash-500 bg-lilac_ash-300 rounded-3xl">
            <CheckCircle className="h-4 w-4 text-lilac_ash-700" />
            <AlertDescription className="text-lilac_ash-800">
              Plik przesłany pomyślnie! Przekierowuję...
            </AlertDescription>
          </Alert>
        )}

        {/* Action Buttons */}
        <div className="flex gap-4 justify-center pt-4">
          <Link href="/">
            <Button
              variant="outline"
              className="px-8 py-6 rounded-3xl border-lilac_ash-300 text-charcoal-600 hover:text-lilac_ash-600 hover:border-lilac_ash-400 transition-colors"
            >
              ← Powrót
            </Button>
          </Link>

          <Button
            onClick={handleUpload}
            disabled={!selectedFile || loading}
            className="px-8 py-6 bg-lilac_ash-500 hover:bg-lilac_ash-600 text-bright_snow-900 font-semibold rounded-3xl disabled:opacity-50 disabled:bg-lilac_ash-300 transition-colors"
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
