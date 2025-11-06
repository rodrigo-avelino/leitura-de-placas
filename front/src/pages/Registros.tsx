// pages/Registros.tsx (Completo e Integrado)

import { useState, useEffect, useMemo, useCallback } from "react";
import Navigation from "@/components/Layout/Navigation";
import FiltrosRegistros from "@/components/Registros/FiltrosRegistros";
import TabelaRegistros, {
  Registro, // A interface Registro deve ser exportada de TabelaRegistros
} from "@/components/Registros/TabelaRegistros";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
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
    tipoPlaca: "TODOS", // Novo filtro
  });

  // 2. Lógica para manter os filtros aplicados ao estado global 'registros'
  const handleFilter = useCallback(
    (
      filters: {
        placa: string;
        dataInicio: string;
        dataFim: string;
        tipoPlaca: string; // Novo parâmetro
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

      // Filtro por tipo de placa
      if (filters.tipoPlaca && filters.tipoPlaca !== "TODOS") {
        filtered = filtered.filter((r) => r.tipo_placa === filters.tipoPlaca);
      }

      // Aplica a ordenação, se necessário (geralmente por dataHora descendente)
      filtered.sort(
        (a, b) => new Date(b.dataHora).getTime() - new Date(a.dataHora).getTime()
      );

      setFilteredRegistros(filtered);
    },
    [registros]
  );

  // Dispara o filtro sempre que 'registros' ou 'currentFilters' muda
  useEffect(() => {
    handleFilter(currentFilters, registros);
  }, [registros, currentFilters, handleFilter]);

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
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/30">
      <Navigation />

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-12 max-w-[1600px]">
        {/* Header */}
        <div className="mb-10 space-y-5">
          <div className="flex justify-between items-center">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <h1 className="text-4xl lg:text-5xl font-bold text-foreground tracking-tight">
                  Consulta de Placas
                </h1>
              </div>
              <p className="text-muted-foreground text-base sm:text-lg">
                Histórico completo de registros processados
              </p>
            </div>
            {/* Indicador de Conexão WebSocket */}
            <div
              className={`flex items-center text-sm font-medium px-4 py-2 rounded-full ${
                wsConnected
                  ? "bg-green-100 dark:bg-green-950/30 text-green-700 dark:text-green-400"
                  : "bg-red-100 dark:bg-red-950/30 text-red-700 dark:text-red-400"
              }`}
            >
              <Wifi
                className={`h-4 w-4 mr-2 ${wsConnected ? "animate-pulse" : ""}`}
              />
              {wsConnected
                ? "LIVE: Tempo Real"
                : "Desconectado"}
            </div>
          </div>

          <Separator className="bg-border/60" />
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
