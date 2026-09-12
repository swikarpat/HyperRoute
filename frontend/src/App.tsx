import { useState, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  useNodesState,
  useEdgesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import axios from 'axios';
import {
  ShieldAlert,
  Cpu,
  Server,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCcw,
  UserCheck,
} from 'lucide-react';

interface IngestAlertPayload {
  account_id: string;
  amount_usd: number;
  sender_country: string;
  receiver_country: string;
  narrative: string;
}

interface IngestAlertResponse {
  workflow_id: string;
  status: string;
  final_fsm_state: number;
  total_steps_executed: number;
  transaction_amount: number;
  gateway_latency_ms: number;
  circuit_breaker_status: string;
}

const initialNodes: Node[] = [
  { id: '1', position: { x: 50, y: 150 }, data: { label: '1: IDLE' }, className: 'bg-slate-800 text-slate-300 border border-slate-700 rounded-lg p-3 text-xs font-mono font-bold shadow-lg' },
  { id: '2', position: { x: 230, y: 150 }, data: { label: '2: INGESTING_ALERT' }, className: 'bg-slate-800 text-slate-300 border border-slate-700 rounded-lg p-3 text-xs font-mono font-bold shadow-lg' },
  { id: '3', position: { x: 440, y: 150 }, data: { label: '3: PARSING_EVIDENCE' }, className: 'bg-slate-800 text-slate-300 border border-slate-700 rounded-lg p-3 text-xs font-mono font-bold shadow-lg' },
  { id: '4', position: { x: 660, y: 150 }, data: { label: '4: EXTRACTING_ACCOUNTS' }, className: 'bg-slate-800 text-slate-300 border border-slate-700 rounded-lg p-3 text-xs font-mono font-bold shadow-lg' },
  { id: '5', position: { x: 890, y: 150 }, data: { label: '5: CORRELATING_HISTORY' }, className: 'bg-slate-800 text-slate-300 border border-slate-700 rounded-lg p-3 text-xs font-mono font-bold shadow-lg' },
  { id: '6', position: { x: 1120, y: 150 }, data: { label: '6: EVALUATING_RISK' }, className: 'bg-slate-800 text-slate-300 border border-slate-700 rounded-lg p-3 text-xs font-mono font-bold shadow-lg' },
  { id: '7', position: { x: 1350, y: 50 }, data: { label: '7: AWAITING_APPROVAL' }, className: 'bg-amber-950/80 text-amber-300 border border-amber-500/50 rounded-lg p-3 text-xs font-mono font-bold shadow-lg' },
  { id: '9', position: { x: 1350, y: 250 }, data: { label: '9: ISSUING_CLEARANCE' }, className: 'bg-slate-800 text-slate-300 border border-slate-700 rounded-lg p-3 text-xs font-mono font-bold shadow-lg' },
];

const initialEdges: Edge[] = [
  { id: 'e1-2', source: '1', target: '2', animated: false, style: { stroke: '#475569' } },
  { id: 'e2-3', source: '2', target: '3', animated: false, style: { stroke: '#475569' } },
  { id: 'e3-4', source: '3', target: '4', animated: false, style: { stroke: '#475569' } },
  { id: 'e4-5', source: '4', target: '5', animated: false, style: { stroke: '#475569' } },
  { id: 'e5-6', source: '5', target: '6', animated: false, style: { stroke: '#475569' } },
  { id: 'e6-7', source: '6', target: '7', label: 'Amount >= $500k', animated: false, style: { stroke: '#f59e0b' }, labelStyle: { fill: '#f59e0b', fontSize: 10 } },
  { id: 'e6-9', source: '6', target: '9', label: 'Amount < $500k', animated: false, style: { stroke: '#10b981' }, labelStyle: { fill: '#10b981', fontSize: 10 } },
];

export default function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<IngestAlertResponse | null>(null);

  const [accountId, setAccountId] = useState('ACC-CORP-4402');
  const [amountUsd, setAmountUsd] = useState<number>(3400000);
  const [narrative, setNarrative] = useState('Urgent multi-entity liquidity transfer across corporate entities.');
  const [humanApproved, setHumanApproved] = useState(false);

  const resetGraph = useCallback(() => {
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        className: 'bg-slate-800 text-slate-300 border border-slate-700 rounded-lg p-3 text-xs font-mono font-bold shadow-lg',
      }))
    );
    setEdges((eds) =>
      eds.map((edge) => ({
        ...edge,
        animated: false,
        style: { stroke: '#475569' },
      }))
    );
    setResponse(null);
    setHumanApproved(false);
  }, [setNodes, setEdges]);

  const runInvestigation = async () => {
    resetGraph();
    setLoading(true);

    try {
      const payload: IngestAlertPayload = {
        account_id: accountId,
        amount_usd: amountUsd,
        sender_country: 'SG',
        receiver_country: 'US',
        narrative: narrative,
      };

      const res = await axios.post<IngestAlertResponse>('http://localhost:8080/api/v1/gateway/alerts', payload);
      setResponse(res.data);

      const finalState = res.data.final_fsm_state;
      const traversed = ['1', '2', '3', '4', '5', '6', finalState.toString()];

      setNodes((nds) =>
        nds.map((node) => {
          if (traversed.includes(node.id)) {
            const isTerminal = node.id === finalState.toString();
            return {
              ...node,
              className: isTerminal
                ? node.id === '7'
                  ? 'bg-amber-600 text-white border-2 border-amber-300 rounded-lg p-3 text-xs font-mono font-bold shadow-[0_0_20px_rgba(245,158,11,0.5)]'
                  : 'bg-emerald-600 text-white border-2 border-emerald-300 rounded-lg p-3 text-xs font-mono font-bold shadow-[0_0_20px_rgba(16,185,129,0.5)]'
                : 'bg-blue-900/80 text-blue-200 border-2 border-blue-500 rounded-lg p-3 text-xs font-mono font-bold shadow-md',
            };
          }
          return node;
        })
      );

      setEdges((eds) =>
        eds.map((edge) => {
          const edgeActive =
            (edge.id === 'e1-2' && traversed.includes('2')) ||
            (edge.id === 'e2-3' && traversed.includes('3')) ||
            (edge.id === 'e3-4' && traversed.includes('4')) ||
            (edge.id === 'e4-5' && traversed.includes('5')) ||
            (edge.id === 'e5-6' && traversed.includes('6')) ||
            (edge.id === 'e6-7' && finalState === 7) ||
            (edge.id === 'e6-9' && finalState === 9);

          return {
            ...edge,
            animated: edgeActive,
            style: edgeActive ? { stroke: '#38bdf8', strokeWidth: 2 } : { stroke: '#475569' },
          };
        })
      );
    } catch (err: any) {
      console.error(err);
      alert('Pipeline Call Failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full w-full bg-slate-950 text-slate-100 select-none">
      <header className="flex items-center justify-between px-6 py-3 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <ShieldAlert className="w-6 h-6 text-cyan-400" />
          <span className="text-sm font-bold tracking-wider uppercase bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
            HyperRoute Mission Control
          </span>
          <span className="text-xs px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800 font-mono">
            v1.0-Enterprise
          </span>
        </div>

        <div className="flex items-center space-x-6 text-xs font-mono">
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <Server className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-300">Gateway :8080</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <Cpu className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-300">C++20 FSM :50051</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <Zap className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-300">ADK Agents :8000</span>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <div className="w-80 p-5 bg-slate-900/60 border-r border-slate-800 flex flex-col justify-between overflow-y-auto">
          <div className="space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Incoming Banking Alert
            </h2>

            <div>
              <label className="block text-[11px] font-mono text-slate-400 mb-1">Account Entity ID</label>
              <input
                type="text"
                value={accountId}
                onChange={(e) => setAccountId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div>
              <label className="block text-[11px] font-mono text-slate-400 mb-1">Transaction Value (USD)</label>
              <input
                type="number"
                value={amountUsd}
                onChange={(e) => setAmountUsd(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">
                Rule: &ge; $500,000 mandates Human Escalation (State 7)
              </span>
            </div>

            <div>
              <label className="block text-[11px] font-mono text-slate-400 mb-1">Wire Transfer Narrative</label>
              <textarea
                rows={3}
                value={narrative}
                onChange={(e) => setNarrative(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <button
              onClick={runInvestigation}
              disabled={loading}
              className="w-full flex items-center justify-center space-x-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium py-2 rounded text-xs transition duration-150 disabled:opacity-50 shadow-md shadow-cyan-950"
            >
              {loading ? (
                <>
                  <RotateCcw className="w-3.5 h-3.5 animate-spin" />
                  <span>Executing Pipeline...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5" />
                  <span>Trigger Investigation</span>
                </>
              )}
            </button>
          </div>

          {response && (
            <div className="mt-4 p-3.5 bg-slate-950 border border-slate-800 rounded-lg space-y-2 text-xs font-mono">
              <div className="flex items-center justify-between text-slate-400">
                <span>Workflow ID</span>
                <span className="text-cyan-400">{response.workflow_id}</span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>Gateway Latency</span>
                <span className="text-emerald-400">{response.gateway_latency_ms} ms</span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>Total Steps</span>
                <span className="text-slate-200">{response.total_steps_executed}</span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>Circuit Breaker</span>
                <span className="text-emerald-400 font-bold">{response.circuit_breaker_status}</span>
              </div>

              {response.final_fsm_state === 7 && (
                <div className="mt-3 pt-3 border-t border-slate-800">
                  <div className="flex items-center space-x-1.5 text-amber-400 mb-2">
                    <AlertTriangle className="w-4 h-4" />
                    <span className="font-bold">Escalated to Human</span>
                  </div>
                  {!humanApproved ? (
                    <button
                      onClick={() => setHumanApproved(true)}
                      className="w-full flex items-center justify-center space-x-1.5 bg-amber-600 hover:bg-amber-500 text-white py-1.5 rounded text-[11px] font-bold"
                    >
                      <UserCheck className="w-3.5 h-3.5" />
                      <span>Authorize Freeze (${(response.transaction_amount / 1_000_000).toFixed(1)}M)</span>
                    </button>
                  ) : (
                    <div className="flex items-center justify-center space-x-1 text-emerald-400 text-[11px]">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Compliance Officer Override Confirmed</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex-1 h-full bg-slate-950 relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            fitView
          >
            <Background color="#1e293b" gap={20} size={1} />
            <Controls className="bg-slate-900 border-slate-800 fill-slate-300" />
          </ReactFlow>
        </div>
      </div>
    </div>
  );
}
