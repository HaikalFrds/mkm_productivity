<?php

namespace App\Livewire;

use App\Models\Absen;
use App\Models\DailyProduction;
use App\Models\DailyReport;
use App\Models\InhouseClaim;
use App\Models\ProblemRecord;
use Carbon\Carbon;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\DB;
use Livewire\Component;

class InputLaporan extends Component
{
    // ── Master data (loaded from v2 Supabase, persisted in Livewire state) ──
    public array $shifts     = [];
    public array $sections   = [];
    public array $shopModels = [];   // [{name, mhu}] per selected section
    public array $opNumbers  = [];   // [string] per selected section
    public array $factors    = [];   // [string] from problem_category

    // Static fallbacks (used when DB returns nothing)
    private const DEFAULT_OP_ST = [
        'CS-10','CS-12','CS-17','CS-18','CS-20',
        'CS-30','CS-40','CS-50','CS-60','CS-70',
    ];
    private const DEFAULT_FACTORS = [
        'Machine','Setting','Man','Tool','Material',
        'Meeting','Quality','Try Cut','Preparation','Others',
    ];
    private const NOTE_TYPES = [
        'Sakit','Izin','Alpa','Cuti','Sholat Jumat','Terlambat','Lainnya',
    ];
    private const SATUAN = ['Unit','Pcs','Set','Lot','Kg','Box','Sheet'];
    private const OT_MAP = ['—' => 0.0, '2H' => 2.0, '3H' => 3.0, '11H' => 11.0];

    // ── Header fields ─────────────────────────────────────────────────────
    public string $shop             = '';
    public string $date             = '';
    public string $dayName          = '';
    public string $shift            = '';
    public string $ot               = '—';
    public bool   $hariPengganti    = false;
    public string $hariPenggantiDay = 'Senin';

    // ── Dynamic rows ──────────────────────────────────────────────────────
    public array $productions = [];
    public array $absences    = [];
    public array $inhouse     = [];
    public array $lineStops   = [];

    // ── Calculation Hour ──────────────────────────────────────────────────
    public float $calcProcess     = 0.0;
    public float $calcPreparation = 0.25;
    public float $calcQuality     = 0.0;
    public float $calcLineStop    = 0.0;
    public float $calcAbsence     = 0.0;
    public float $calcSholat      = 0.1667;
    public float $calcTotal       = 8.0;
    public float $calcBalance     = 0.0;
    public bool  $calcBalanceOk   = false;

    // ── Save state ────────────────────────────────────────────────────────
    public bool    $balanceWarning  = false;   // true = show balance confirm UI
    public ?string $successMessage  = null;
    public ?string $errorMessage    = null;

    // ─────────────────────────────────────────────────────────────────────

    public function mount(): void
    {
        $this->loadShiftData();
        $this->loadSectionData();
        $this->loadFactorData();

        // Default to first shift
        if (!empty($this->shifts)) {
            $this->shift = $this->shifts[0]['name'];
        }

        $this->date = today()->format('Y-m-d');
        $this->updateDayName();

        // Start with 3 empty rows in each active table
        for ($i = 0; $i < 3; $i++) {
            $this->productions[] = $this->emptyProductionRow();
            $this->absences[]    = $this->emptyAbsenceRow();
        }
    }

    // ── Master data loaders ───────────────────────────────────────────────

    private function loadShiftData(): void
    {
        try {
            $this->shifts = DB::connection('v2')
                ->table('shift')
                ->select('id', 'name', 'total_hours', 'preparation_min', 'other_min')
                ->orderBy('id')
                ->get()
                ->map(fn ($s) => [
                    'id'              => $s->id,
                    'name'            => $s->name,
                    'total_hours'     => (float) $s->total_hours,
                    'preparation_min' => (float) $s->preparation_min,
                    'other_min'       => (float) $s->other_min,
                ])
                ->toArray();
        } catch (\Throwable) {
            $this->shifts = [
                ['id' => 1, 'name' => 'Day Shift',   'total_hours' => 8.0, 'preparation_min' => 15.0, 'other_min' => 10.0],
                ['id' => 2, 'name' => 'Night Shift',  'total_hours' => 7.0, 'preparation_min' => 15.0, 'other_min' => 10.0],
            ];
        }
    }

    private function loadSectionData(): void
    {
        try {
            $this->sections = DB::connection('v2')
                ->table('section')
                ->select('id', 'name')
                ->orderBy('name')
                ->get()
                ->map(fn ($s) => ['id' => $s->id, 'name' => $s->name])
                ->toArray();
        } catch (\Throwable) {
            $this->sections = [];
        }
    }

    private function loadFactorData(): void
    {
        try {
            $names = DB::connection('v2')
                ->table('problem_category')
                ->join('problem_group', 'problem_group.id', '=', 'problem_category.group_id')
                ->orderBy('problem_category.group_id')
                ->orderBy('problem_category.order_num')
                ->pluck('problem_category.name')
                ->toArray();
            $this->factors = !empty($names) ? $names : self::DEFAULT_FACTORS;
        } catch (\Throwable) {
            $this->factors = self::DEFAULT_FACTORS;
        }
    }

    /**
     * Load shop_models and op_numbers for the currently selected section.
     * Called when shop changes and on mount (if shop already set).
     */
    private function loadShopMasterData(): void
    {
        $sectionId = $this->getCurrentSectionId();
        if ($sectionId === null) {
            $this->shopModels = [];
            $this->opNumbers  = [];
            return;
        }

        try {
            $this->shopModels = DB::connection('v2')
                ->table('shop_model')
                ->where('section_id', $sectionId)
                ->orderBy('model_name')
                ->get(['model_name', 'working_hour'])
                ->map(fn ($r) => [
                    'name' => $r->model_name,
                    'mhu'  => (float) $r->working_hour,
                ])
                ->toArray();
        } catch (\Throwable) {
            $this->shopModels = [];
        }

        try {
            $ops = DB::connection('v2')
                ->table('op_number')
                ->where('section_id', $sectionId)
                ->orderBy('op_no')
                ->pluck('op_no')
                ->toArray();
            $this->opNumbers = !empty($ops) ? $ops : self::DEFAULT_OP_ST;
        } catch (\Throwable) {
            $this->opNumbers = self::DEFAULT_OP_ST;
        }
    }

    private function getCurrentSectionId(): ?int
    {
        $found = collect($this->sections)->firstWhere('name', $this->shop);
        return $found ? (int) $found['id'] : null;
    }

    private function getMhu(string $modelName): float
    {
        $found = collect($this->shopModels)->firstWhere('name', $modelName);
        return $found ? (float) $found['mhu'] : 0.0;
    }

    // ── Livewire lifecycle hooks ──────────────────────────────────────────

    /** Fires after $shop changes → reload models + op numbers for new section */
    public function updatedShop(): void
    {
        $this->loadShopMasterData();
    }

    /**
     * Fires after any property changes via wire:model.
     * Used for auto-fill: Plan H / Act H, Inhouse Hour, Line Stop Stop.
     */
    public function updated(string $name, mixed $value): void
    {
        // ── Production: Plan Qty → Plan H ────────────────────────────────
        if (preg_match('/^productions\.(\d+)\.plan_qty$/', $name, $m)) {
            $i   = (int) $m[1];
            $mhu = $this->getMhu($this->productions[$i]['model'] ?? '');
            if ($mhu > 0 && is_numeric($value) && (float) $value > 0) {
                $this->productions[$i]['plan_h'] = round((float) $value * $mhu, 6);
            }
        }

        // ── Production: Act Qty → Act H ──────────────────────────────────
        if (preg_match('/^productions\.(\d+)\.act_qty$/', $name, $m)) {
            $i   = (int) $m[1];
            $mhu = $this->getMhu($this->productions[$i]['model'] ?? '');
            if ($mhu > 0 && is_numeric($value) && (float) $value > 0) {
                $this->productions[$i]['act_h'] = round((float) $value * $mhu, 6);
            }
        }

        // ── Production: Model changed → re-fill H values ─────────────────
        if (preg_match('/^productions\.(\d+)\.model$/', $name, $m)) {
            $i   = (int) $m[1];
            $mhu = $this->getMhu((string) $value);
            if ($mhu > 0) {
                $pq = (float) ($this->productions[$i]['plan_qty'] ?: 0);
                $aq = (float) ($this->productions[$i]['act_qty']  ?: 0);
                if ($pq > 0) $this->productions[$i]['plan_h'] = round($pq * $mhu, 6);
                if ($aq > 0) $this->productions[$i]['act_h']  = round($aq * $mhu, 6);
            }
        }

        // ── Line Stop: Start or End → auto-calc Stop ─────────────────────
        if (preg_match('/^lineStops\.(\d+)\.(start|end)$/', $name, $m)) {
            $this->calcLineStopStop((int) $m[1]);
        }

        // ── Inhouse: Qty → auto-calc Hour ────────────────────────────────
        if (preg_match('/^inhouse\.(\d+)\.qty$/', $name, $m)) {
            $i   = (int) $m[1];
            $mhu = $this->getMhu($this->inhouse[$i]['model'] ?? '');
            if ($mhu > 0 && is_numeric($value) && (float) $value > 0) {
                $this->inhouse[$i]['hour'] = round((float) $value * $mhu, 6);
            }
        }

        // ── Inhouse: Model changed → re-fill Hour ────────────────────────
        if (preg_match('/^inhouse\.(\d+)\.model$/', $name, $m)) {
            $i   = (int) $m[1];
            $mhu = $this->getMhu((string) $value);
            if ($mhu > 0) {
                $qty = (float) ($this->inhouse[$i]['qty'] ?: 0);
                if ($qty > 0) $this->inhouse[$i]['hour'] = round($qty * $mhu, 6);
            }
        }
    }

    /** Auto-calc Line Stop "Stop" = (end - start) in hours */
    private function calcLineStopStop(int $idx): void
    {
        $start = $this->lineStops[$idx]['start'] ?? '';
        $end   = $this->lineStops[$idx]['end']   ?? '';
        if (!filled($start) || !filled($end)) return;
        try {
            [$sh, $sm] = array_map('intval', explode(':', $start));
            [$eh, $em] = array_map('intval', explode(':', $end));
            $diffMin = ($eh * 60 + $em) - ($sh * 60 + $sm);
            if ($diffMin < 0) $diffMin += 1440;   // overnight
            $this->lineStops[$idx]['stop'] = round($diffMin / 60, 4);
        } catch (\Throwable) {
        }
    }

    // ── Date navigation ───────────────────────────────────────────────────

    public function prevDate(): void
    {
        $this->date = Carbon::parse($this->date)->subDay()->format('Y-m-d');
        $this->updateDayName();
    }

    public function nextDate(): void
    {
        $this->date = Carbon::parse($this->date)->addDay()->format('Y-m-d');
        $this->updateDayName();
    }

    public function updatedDate(): void
    {
        $this->updateDayName();
    }

    private function updateDayName(): void
    {
        $hari = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'];
        try {
            $this->dayName = $hari[Carbon::parse($this->date)->dayOfWeek];
        } catch (\Throwable) {
            $this->dayName = '';
        }
    }

    // ── Row templates ─────────────────────────────────────────────────────

    private function emptyProductionRow(): array
    {
        $first = !empty($this->shopModels) ? $this->shopModels[0]['name'] : '';
        return ['model' => $first, 'plan_qty' => '', 'act_qty' => '', 'plan_h' => '', 'act_h' => ''];
    }

    private function emptyAbsenceRow(): array
    {
        return ['nik' => '', 'name' => '', 'note' => self::NOTE_TYPES[0], 'hour' => ''];
    }

    private function emptyInhouseRow(): array
    {
        $first = !empty($this->shopModels) ? $this->shopModels[0]['name'] : '';
        $op    = !empty($this->opNumbers)  ? $this->opNumbers[0]          : '';
        $fac   = !empty($this->factors)    ? $this->factors[0]            : 'Machine';
        return [
            'model'  => $first, 'op_st'  => $op,  'item'   => '',     'qty'    => '',
            'satuan' => 'Unit',  'cause'  => '',   'action' => '',
            'factor' => $fac,   'hour'   => '',    'lost'   => '',     'status' => '',
        ];
    }

    private function emptyLineStopRow(): array
    {
        $first = !empty($this->shopModels) ? $this->shopModels[0]['name'] : '';
        $op    = !empty($this->opNumbers)  ? $this->opNumbers[0]          : '';
        $fac   = !empty($this->factors)    ? $this->factors[0]            : 'Machine';
        return [
            'model'   => $first, 'op_st'  => $op,  'problem' => '',
            'cause'   => '',     'action' => '',    'factor'  => $fac,
            'start'   => '',     'end'    => '',    'stop'    => '',    'lost' => '',
        ];
    }

    // ── Add / Remove row actions ──────────────────────────────────────────

    public function addProductionRow(): void    { $this->productions[] = $this->emptyProductionRow(); }
    public function addAbsenceRow(): void       { $this->absences[]    = $this->emptyAbsenceRow(); }
    public function addInhouseRow(): void       { $this->inhouse[]     = $this->emptyInhouseRow(); }
    public function addLineStopRow(): void      { $this->lineStops[]   = $this->emptyLineStopRow(); }

    public function removeLastProductionRow(): void
    {
        if (count($this->productions) > 1) { array_pop($this->productions); $this->productions = array_values($this->productions); }
    }

    public function removeLastAbsenceRow(): void
    {
        if (count($this->absences) > 1) { array_pop($this->absences); $this->absences = array_values($this->absences); }
    }

    public function removeLastInhouseRow(): void
    {
        if (!empty($this->inhouse)) { array_pop($this->inhouse); $this->inhouse = array_values($this->inhouse); }
    }

    public function removeLastLineStopRow(): void
    {
        if (!empty($this->lineStops)) { array_pop($this->lineStops); $this->lineStops = array_values($this->lineStops); }
    }

    // ── Shift / Hour calculation ──────────────────────────────────────────

    private function getShiftData(): array
    {
        return collect($this->shifts)->firstWhere('name', $this->shift) ?? [
            'total_hours' => 8.0, 'preparation_min' => 15.0, 'other_min' => 10.0,
        ];
    }

    private function computeEffectiveHours(): float
    {
        $data = $this->getShiftData();
        $base = (float) $data['total_hours'];

        $effectiveDay = ($this->hariPengganti && filled($this->hariPenggantiDay))
            ? $this->hariPenggantiDay
            : $this->dayName;

        // Jumat deduction for Day Shift
        if ($effectiveDay === 'Jumat'
            && !str_contains(strtolower($this->shift), 'night')
            && $base > 0) {
            $base -= 0.5;
        }

        $base += self::OT_MAP[$this->ot] ?? 0.0;
        return round($base, 4);
    }

    private function computeCalcHours(): void
    {
        $shiftData = $this->getShiftData();

        $this->calcTotal       = $this->computeEffectiveHours();
        $this->calcPreparation = round((float) $shiftData['preparation_min'] / 60, 4);
        $this->calcSholat      = round((float) $shiftData['other_min'] / 60, 4);

        $this->calcProcess  = collect($this->productions)->sum(fn ($r) => (float) ($r['act_h'] ?: 0));
        $this->calcAbsence  = collect($this->absences)->sum(fn ($r)   => (float) ($r['hour']  ?: 0));
        $this->calcLineStop = collect($this->lineStops)->sum(fn ($r)  => (float) ($r['lost']  ?: 0));
        $this->calcQuality  = collect($this->inhouse)->sum(fn ($r)    => (float) ($r['lost']  ?: 0));

        $this->calcBalance = $this->calcTotal
            - $this->calcProcess
            - $this->calcPreparation
            - $this->calcQuality
            - $this->calcLineStop
            - $this->calcAbsence
            - $this->calcSholat;

        $this->calcBalanceOk = abs($this->calcBalance) < 0.001;
    }

    // ── Save (with v2-style validation) ──────────────────────────────────

    public function save(): void
    {
        $this->successMessage  = null;
        $this->errorMessage    = null;
        $this->balanceWarning  = false;
        $this->computeCalcHours();

        // ① Section required
        if (empty(trim($this->shop))) {
            $this->errorMessage = 'Pilih section terlebih dahulu.';
            return;
        }

        // ② At least one production row with data
        $hasProd = collect($this->productions)->contains(
            fn ($r) => filled($r['model']) || filled($r['act_qty'])
        );
        if (!$hasProd) {
            $this->errorMessage = 'Tambahkan minimal 1 baris data produksi.';
            return;
        }

        // ③ Balance warning (ask confirmation, like v2)
        if (!$this->calcBalanceOk) {
            $this->balanceWarning = true;
            return;
        }

        $this->doSave();
    }

    /** Saves unconditionally — called from "Tetap Simpan" after balance warning */
    public function forceSave(): void
    {
        $this->balanceWarning = false;
        $this->computeCalcHours();
        $this->doSave();
    }

    public function cancelSave(): void
    {
        $this->balanceWarning = false;
    }

    private function doSave(): void
    {
        try {
            DB::transaction(function () {
                $report = DailyReport::create([
                    'user_id'        => Auth::id(),
                    'date'           => $this->date,
                    'shift'          => $this->shift,
                    'section'        => $this->shop,
                    'hour'           => $this->calcTotal,
                    'ot'             => self::OT_MAP[$this->ot] ?? 0.0,
                    'hari_pengganti' => $this->hariPengganti,
                    'status'         => 'submitted',
                ]);

                foreach ($this->productions as $row) {
                    if (filled($row['model']) || filled($row['act_qty'])) {
                        DailyProduction::create([
                            'report_id'    => $report->id,
                            'model'        => $row['model'],
                            'plan_unit'    => (float) ($row['plan_qty'] ?: 0),
                            'actual_unit'  => (float) ($row['act_qty']  ?: 0),
                            'plan_whour'   => (float) ($row['plan_h']   ?: 0),
                            'actual_whour' => (float) ($row['act_h']    ?: 0),
                        ]);
                    }
                }

                foreach ($this->absences as $row) {
                    if (filled($row['nik']) || filled($row['name'])) {
                        Absen::create([
                            'report_id'  => $report->id,
                            'nik_absen'  => $row['nik'],
                            'nama'       => $row['name'],
                            'keterangan' => $row['note'],
                            'hour'       => (float) ($row['hour'] ?: 0),
                        ]);
                    }
                }

                foreach ($this->inhouse as $row) {
                    if (filled($row['model']) || filled($row['item'])) {
                        InhouseClaim::create([
                            'report_id'    => $report->id,
                            'model'        => $row['model'],
                            'op_no_st'     => $row['op_st'],
                            'item'         => $row['item'],
                            'qty'          => (float) ($row['qty']  ?: 0),
                            'satuan'       => $row['satuan'],
                            'penyebab'     => $row['cause'],
                            'tindakan'     => $row['action'],
                            'faktor'       => $row['factor'],
                            'stop_hr'      => (float) ($row['hour'] ?: 0),
                            'lost_hr'      => (float) ($row['lost'] ?: 0),
                            'status_klaim' => $row['status'],
                        ]);
                    }
                }

                foreach ($this->lineStops as $row) {
                    if (filled($row['problem']) || filled($row['model'])) {
                        ProblemRecord::create([
                            'report_id'         => $report->id,
                            'model'             => $row['model'],
                            'op_st'             => $row['op_st'],
                            'description'       => $row['problem'],
                            'cause'             => $row['cause'],
                            'corrective_action' => $row['action'],
                            'factor'            => $row['factor'],
                            'start_time'        => filled($row['start']) ? $row['start'] : null,
                            'end_time'          => filled($row['end'])   ? $row['end']   : null,
                            'down_time'         => (float) ($row['stop'] ?: 0),
                            'loss_time'         => (float) ($row['lost'] ?: 0),
                        ]);
                    }
                }
            });

            $this->successMessage = 'Laporan berhasil disimpan.';
            $this->resetForm();

        } catch (\Throwable $e) {
            $this->errorMessage = 'Gagal menyimpan: ' . $e->getMessage();
        }
    }

    // ── Reset ─────────────────────────────────────────────────────────────

    public function resetForm(): void
    {
        $this->shop             = '';
        $this->shift            = !empty($this->shifts) ? $this->shifts[0]['name'] : '';
        $this->ot               = '—';
        $this->hariPengganti    = false;
        $this->hariPenggantiDay = 'Senin';
        $this->date             = today()->format('Y-m-d');
        $this->balanceWarning   = false;
        $this->updateDayName();
        $this->shopModels       = [];
        $this->opNumbers        = [];
        $this->productions      = [];
        $this->absences         = [];
        $this->inhouse          = [];
        $this->lineStops        = [];

        for ($i = 0; $i < 3; $i++) {
            $this->productions[] = $this->emptyProductionRow();
            $this->absences[]    = $this->emptyAbsenceRow();
        }
    }

    // ─────────────────────────────────────────────────────────────────────

    public function render()
    {
        $this->computeCalcHours();
        return view('livewire.input-laporan')
            ->layout('components.layouts.app', ['title' => 'Input Laporan Harian']);
    }
}
