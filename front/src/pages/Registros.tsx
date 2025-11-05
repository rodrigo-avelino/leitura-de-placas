// pages/Registros.tsx (Completo e Integrado)

import { useState, useEffect, useMemo, useCallback } from "react";
import Navigation from "@/components/Layout/Navigation";
import FiltrosRegistros from "@/components/Registros/FiltrosRegistros";
import TabelaRegistros, {
  Registro, // A interface Registro deve ser exportada de TabelaRegistros
} from "@/components/Registros/TabelaRegistros";
import { Card, CardContent } from "@/components/ui/card";
import {
  BarChart3,
  FileText,
  TrendingUp,
  Clock,
  Wifi,
  Loader2,
} from "lucide-react";

// --- Importação do Novo Hook ---
import { useRegistroWebSocket } from "@/hooks/useRegistroWebSocket";

const Registros = () => {
  // 1. Usar o hook para gerenciar dados e WebSocket
  const {
    registros,
    isLoading,
    wsConnected,
    deleteRegistro, // Função real de exclusão via API
    deleteStatus, // Status do processamento de exclusão
  } = useRegistroWebSocket();

  const [filteredRegistros, setFilteredRegistros] = useState<Registro[]>([]);
  const [currentFilters, setCurrentFilters] = useState({
    placa: "",
    dataInicio: "",
    dataFim: "",
  });

  // 2. Lógica para manter os filtros aplicados ao estado global 'registros'
  // Dispara o filtro sempre que 'registros' muda (novo registro via WS)
  useEffect(() => {
    handleFilter(currentFilters, registros);
  }, [registros]);

  const handleFilter = (
    filters: {
      placa: string;
      dataInicio: string;
      dataFim: string;
    },
    sourceRegistros: Registro[] = registros
  ) => {
    setCurrentFilters(filters);
    let filtered = [...sourceRegistros];

    if (filters.placa) {
      filtered = filtered.filter((r) =>
        r.placa.toUpperCase().includes(filters.placa.toUpperCase())
      );
    }

    if (filters.dataInicio) {
      const dataInicio = new Date(filters.dataInicio);
      filtered = filtered.filter((r) => new Date(r.dataHora) >= dataInicio);
    }

    if (filters.dataFim) {
      const dataFim = new Date(filters.dataFim);
      // Ajusta a hora para incluir todo o dia final
      dataFim.setHours(23, 59, 59, 999);
      filtered = filtered.filter((r) => new Date(r.dataHora) <= dataFim);
    }

    // Aplica a ordenação, se necessário (geralmente por dataHora descendente)
    filtered.sort(
      (a, b) => new Date(b.dataHora).getTime() - new Date(a.dataHora).getTime()
    );

    setFilteredRegistros(filtered);
  };

  // 3. Lógica de DELETE (Usando a função do hook)
  const handleDelete = async (id: number | string) => {
    const confirmDelete = window.confirm(
      `Tem certeza que deseja deletar o registro ID ${id}?`
    );
    if (!confirmDelete) return;

    // Chama a função de deleção real do hook. O hook cuida da atualização do estado 'registros'.
    const success = await deleteRegistro(id);

    if (success) {
      console.log(`Registro ID ${id} deletado com sucesso.`);
    } else {
      alert(`Erro ao deletar o registro ID ${id}. Verifique a API.`);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8 flex justify-between items-center">
          <h1 className="text-4xl font-bold text-foreground mb-2 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Consulta de Placas
          </h1>
          {/* Indicador de Conexão WebSocket */}
          <div
            className={`flex items-center text-sm font-medium p-2 rounded-full ${
              wsConnected
                ? "bg-green-100 text-green-700"
                : "bg-red-100 text-red-700"
            }`}
          >
            <Wifi
              className={`h-4 w-4 mr-2 ${wsConnected ? "animate-pulse" : ""}`}
            />
            {wsConnected
              ? "LIVE: Registros em Tempo Real"
              : "WebSocket Desconectado"}
          </div>
        </div>

        {/* Filtros */}
        <div className="mb-6">
          <FiltrosRegistros onFilter={(filters) => handleFilter(filters)} />
        </div>

        {/* Grid de Registros */}
        {isLoading ? (
          <Card>
            <CardContent className="p-8 text-center text-gray-500">
              <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
              Carregando registros históricos...
            </CardContent>
          </Card>
        ) : (
          <TabelaRegistros
            registros={filteredRegistros}
            onDelete={handleDelete}
            // Passando o status de deleção para que a tabela possa desabilitar botões
            deleteStatus={deleteStatus}
          />
        )}
      </main>
    </div>
  );
};

export default Registros;
