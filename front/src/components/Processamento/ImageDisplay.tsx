import React from "react";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, Zap, RotateCcw, CheckCircle, XCircle } from "lucide-react";

// --- INTERFACE CORRIGIDA ---
interface ImageDisplayProps {
  // Input/Visualização
  imageUrl: string | null;

  // Output das Imagens (Podem ser nulas se o processamento não tiver chegado lá)
  croppedPlate: string | null;
  binarizedImage: string | null;
  segmentedImage: string | null;
  placaLida: string | null; // <<< Agora aceita null

  // Controles e Status
  onClear: () => void;
  onProcess: () => void;
  isProcessing: boolean;
  status: "idle" | "running" | "success" | "failed";
}

const ImageDisplay: React.FC<ImageDisplayProps> = ({
  imageUrl,
  croppedPlate,
  binarizedImage,
  segmentedImage,
  placaLida,
  onClear,
  onProcess,
  isProcessing,
  status,
}) => {
  const getStatusColor = (currentStatus: typeof status) => {
    switch (currentStatus) {
      case "running":
        return "border-blue-500 bg-blue-50 text-blue-800";
      case "success":
        return "border-green-500 bg-green-50 text-green-800";
      case "failed":
        return "border-red-500 bg-red-50 text-red-800";
      default:
        return "border-gray-300 bg-white text-gray-700";
    }
  };

  const getStatusText = (currentStatus: typeof status) => {
    switch (currentStatus) {
      case "running":
        return "PROCESSANDO...";
      case "success":
        return `SUCESSO! Placa: ${placaLida || "N/A"}`;
      case "failed":
        return "FALHA NA DETECÇÃO";
      default:
        return "PRONTO PARA ANÁLISE";
    }
  };

  return (
    <Card className={`shadow-xl transition-all ${getStatusColor(status)}`}>
      <CardHeader className="p-4 border-b">
        <CardTitle className="flex items-center justify-between text-lg">
          Imagem Atual
          <span className="text-sm font-semibold uppercase">
            {getStatusText(status)}
          </span>
        </CardTitle>
      </CardHeader>

      <CardContent className="p-4 space-y-4">
        {/* Imagem Principal */}
        <div className="relative w-full aspect-video rounded-lg overflow-hidden border">
          {imageUrl ? (
            <img
              src={imageUrl}
              alt="Imagem Original"
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gray-200 text-gray-500">
              Nenhuma imagem selecionada.
            </div>
          )}

          {isProcessing && (
            <div className="absolute inset-0 bg-black bg-opacity-30 flex items-center justify-center">
              <Loader2 className="h-10 w-10 text-white animate-spin" />
            </div>
          )}
        </div>

        {/* Miniaturas de Processamento (Recorte, Binarização, Segmentação) */}
        <div className="grid grid-cols-3 gap-2">
          <ImageThumbnail title="Recorte (Candidato)" image={croppedPlate} />
          <ImageThumbnail title="Binarização (Final)" image={binarizedImage} />
          <ImageThumbnail title="Segmentação (Final)" image={segmentedImage} />
        </div>
      </CardContent>

      <CardFooter className="flex justify-between p-4 border-t">
        <Button
          onClick={onClear}
          variant="outline"
          disabled={isProcessing}
          className="text-gray-600 hover:bg-gray-100"
        >
          <RotateCcw className="mr-2 h-4 w-4" /> Limpar
        </Button>

        <Button
          onClick={onProcess}
          disabled={!imageUrl || isProcessing}
          className="bg-indigo-600 hover:bg-indigo-700 transition-colors"
        >
          {isProcessing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processando...
            </>
          ) : (
            <>
              <Zap className="mr-2 h-4 w-4" />
              Iniciar Análise
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  );
};

// Sub-componente para Miniaturas
const ImageThumbnail: React.FC<{ title: string; image: string | null }> = ({
  title,
  image,
}) => (
  <div className="text-center">
    <p className="text-xs text-gray-500 mb-1 font-medium">{title}</p>
    <div className="w-full aspect-video border rounded-md overflow-hidden bg-gray-100 flex items-center justify-center">
      {image ? (
        <img src={image} alt={title} className="w-full h-full object-contain" />
      ) : (
        <span className="text-xs text-gray-400 p-1">Aguardando...</span>
      )}
    </div>
  </div>
);

export default ImageDisplay;
