import { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";

// --- CONFIGURAÇÃO DA API ---
const API_BASE_URL = "http://127.0.0.1:8000";
const WS_URL = "ws://127.0.0.1:8000/ws/registros";

// Defina a interface de Registro
export interface Registro {
  id: number | string;
  placa: string;
  dataHora: string;
  imagemUrl: string;
  tipo_placa?: string;
}

type ProcessingStatus = "idle" | "running" | "success" | "failed";

// Interface de Retorno do Hook
interface WebSocketReturn {
  registros: Registro[];
  isLoading: boolean;
  wsConnected: boolean;
  deleteRegistro: (id: number | string) => Promise<boolean>;
  deleteStatus: ProcessingStatus;
}

export const useRegistroWebSocket = (): WebSocketReturn => {
  const [registros, setRegistros] = useState<Registro[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [deleteStatus, setDeleteStatus] = useState<ProcessingStatus>("idle");
  const wsRef = useRef<WebSocket | null>(null);

  // Mapeador de campo
  const mapBackendToFrontend = (data: any): Registro => ({
    id: data.id || data.id_registro, // Usa o ID do DB
    placa: data.placa,
    dataHora: data.data,
    imagemUrl: data.imagem,
    tipo_placa: data.tipo_placa,
  });

  // --- 1. BUSCA INICIAL (HTTP) ---
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const response = await axios.get<any[]>(
          `${API_BASE_URL}/api/v1/registros`
        );
        const mappedData = response.data.map(mapBackendToFrontend);
        setRegistros(mappedData);
      } catch (error) {
        console.error("Erro ao buscar registros históricos:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchInitialData();
  }, []);

  // --- 2. CONEXÃO WEBSOCKET (LIVE UPDATES) ---
  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.placa && (data.id || data.id_registro)) {
          // Verifica se tem ID
          const novoRegistro = mapBackendToFrontend(data);
          // Adiciona o novo registro ao topo da lista em tempo real
          setRegistros((prev) => [novoRegistro, ...prev]);
        }
      } catch (error) {
        console.error("Erro ao processar mensagem WS:", error);
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
    };

    ws.onerror = (error) => {
      console.error("Erro no WS de Registros:", error);
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // --- 3. LÓGICA DE DELETE (HTTP) ---
  const deleteRegistro = useCallback(async (id: number | string) => {
    setDeleteStatus("running");
    try {
      // Chamada de DELETE para o backend (ajustar URL se necessário)
      const response = await axios.delete(
        `${API_BASE_URL}/api/v1/registros/${id}`
      );

      // O backend deve retornar 200/204, ou um JSON indicando sucesso
      if (response.status === 200 || response.status === 204) {
        // Remove da UI localmente após sucesso
        setRegistros((prev) => prev.filter((r) => r.id !== id));
        setDeleteStatus("success");
        return true;
      } else {
        setDeleteStatus("failed");
        return false;
      }
    } catch (error) {
      console.error("Erro ao deletar registro:", error);
      setDeleteStatus("failed");
      return false;
    } finally {
      setTimeout(() => setDeleteStatus("idle"), 2000);
    }
  }, []);

  return {
    registros,
    isLoading,
    wsConnected,
    deleteRegistro,
    deleteStatus,
  };
};
