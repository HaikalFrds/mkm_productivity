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
    // ── Master data (loaded once in mount, persisted as Livewire state) ───
    public array $shifts   = [];
    public array $sections = [];

    // ── Header fields ────────────────────────────────────────────────────
    public string $shop             = '';
    public string $date             = '';
    public string $dayName          = '';
    public string $shift            = '';
    public string $ot               = '—';
    public bool   $hariPengganti    = false;
    public string $hariPenggantiDay = 'Senin';

    // ── Dynamic rows ─────────────────────────────────────────────────────
    public array $productions = [];
    public array $absences    = [];
    public array $inhouse     = [];
    public array $lineStops   = [];

    // ── Calculation Hour (recomputed on every render) ─────────────────────
    public float $calcProcess     = 0.0;
    public float $calcPreparation = 0.25;
    public float $calcQuality     = 0.0;
    public float $calcLineStop    = 0.0;
    public float $calcAbsence     = 0.0;
    public float $calcSholat      = 0.1667;
    public float $calcTotal       = 8.0;
    public float $calcBalance     = 0.0;
    public bool  $calcBalanceOk   = false;

    // ── Flash messages ────────────────────────────────────────────────────
    public ?string $successMessage = null;
    public ?string $errorMessage   = null;

    // ─────────────────────────────────────────────────────────────────────

    public function mount(): void
    {
        // Load shift master data from v2 Supabase tables (no v3_ prefix)
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
            // Fallback: hardcoded defaults if DB is unreachable
            $this->shifts = [
                ['id' => 1, 'name' => 'Day Shift',  'total_hours' => 8.0, 'preparation_min' => 15.0, 'other_min' => 10.0],
                ['id' => 2, 'name' => 'Night Shift', 'total_hours' => 7.0, 'preparation_min' => 15.0, 'other_min' => 10.0],
            ];
        }

        // Load section master data
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

        // Default to first shift
        if (!empty($this->shifts)) {
            $this->shift = $this->shifts[0]['name'];
        }

        $this->date = today()->format('Y-m-d');
        $this->updateDayName();

        for ($i = 0; $i < 3; $i++) {
            $this->productions[] = $this->emptyProductionRow();
            $this->absences[]    = $this->emptyAbsenceRow();
        }
    }

    // ── Date navigation ──────────────────────────────────────────────────

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

    // ── Row templates ────────────────────────────────────────────────────

    private function emptyProductionRow(): array
    {
        return ['model' => '', 'plan_qty' => '', 'act_qty' => '', 'plan_h' => '', 'act_h' => ''];
    }

    private function emptyAbsenceRow(): array
    {
        return ['nik' => '', 'name' => '', 'note' => 'Sakit', 'hour' => ''];
    }

    private function emptyInhouseRow(): array
    {
        return [
            'model'  => '', 'op_st'  => '', 'item'   => '', 'qty'    => '',
            'satuan' => 'Unit', 'cause' => '', 'action' => '',
            'factor' => 'Machine', 'hour' => '', 'lost' => '', 'status' => '',
        ];
    }

    private function emptyLineStopRow(): array
    {
        return [
            'model'   => '', 'op_st'  => '', 'problem' => '',
            'cause'   => '', 'action' => '', 'factor'  => 'Machine',
            'start'   => '', 'end'    => '', 'stop'    => '', 'lost'   => '',
        ];
    }

    // ── Add / Remove row actions ─────────────────────────────────────────

    public function addProductionRow(): void    { $this->productions[] = $this->emptyProductionRow(); }
    public function addAbsenceRow(): void       { $this->absences[]    = $this->emptyAbsenceRow(); }
    public function addInhouseRow(): void       { $this->inhouse[]     = $this->emptyInhouseRow(); }
    public function addLineStopRow(): void      { $this->lineStops[]   = $this->emptyLineStopRow(); }

    public function removeLastProductionRow(): void
    {
        if (count($this->productions) > 1) {
            array_pop($this->productions);
            $this->productions = array_values($this->productions);
        }
    }

    public function removeLastAbsenceRow(): void
    {
        if (count($this->absences) > 1) {
            array_pop($this->absences);
            $this->absences = array_values($this->absences);
        }
    }

    public function removeLastInhouseRow(): void
    {
        if (!empty($this->inhouse)) {
            array_pop($this->inhouse);
            $this->inhouse = array_values($this->inhouse);
        }
    }

    public function removeLastLineStopRow(): void
    {
        if (!empty($this->lineStops)) {
            array_pop($this->lineStops);
            $this->lineStops = array_values($this->lineStops);
        }
    }

    // ── Shift data helpers ───────────────────────────────────────────────

    /**
     * Returns the shift config array for the currently selected shift name.
     */
    private function getShiftData(): array
    {
        $found = collect($this->shifts)->firstWhere('name', $this->shift);
        return $found ?? [
            'total_hours'     => 8.0,
            'preparation_min' => 15.0,
            'other_min'       => 10.0,
        ];
    }

    /**
     * Computes effective working hours:
     *   base = shift.total_hours
     *   - 0.5h if Friday AND Day Shift
     *   + OT hours (0 / 2 / 3 / 11)
     */
    private function computeEffectiveHours(): float
    {
        $data = $this->getShiftData();
        $base = (float) $data['total_hours'];

        // Determine effective day (hari pengganti overrides the calendar day)
        $effectiveDay = $this->hariPengganti && filled($this->hariPenggantiDay)
            ? $this->hariPenggantiDay
            : $this->dayName;

        $isFriday   = $effectiveDay === 'Jumat';
        $isDayShift = !str_contains(strtolower($this->shift), 'night');
        if ($isFriday && $isDayShift && $base > 0) {
            $base -= 0.5;
        }

        $otMap  = ['—' => 0.0, '2H' => 2.0, '3H' => 3.0, '11H' => 11.0];
        $base  += $otMap[$this->ot] ?? 0.0;

        return round($base, 4);
    }

    // ── Compute Calculation Hour panel ───────────────────────────────────

    private function computeCalcHours(): void
    {
        $shiftData = $this->getShiftData();

        $this->calcTotal       = $this->computeEffectiveHours();
        $this->calcPreparation = round((float) $shiftData['preparation_min'] / 60, 4);
        $this->calcSholat      = round((float) $shiftData['other_min'] / 60, 4);

        $this->calcProcess  = collect($this->productions)->sum(fn ($r) => (float) ($r['act_h'] ?: 0));
        $this->calcAbsence  = collect($this->absences)->sum(fn ($r)   => (float) ($r['hour']  ?: 0));
        // ⚠ Use LOST (col 10) not Stop (col 9) — matching v2 behaviour
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

    // ── OT map helper ────────────────────────────────────────────────────

    private function otToFloat(): float
    {
        return ['—' => 0.0, '2H' => 2.0, '3H' => 3.0, '11H' => 11.0][$this->ot] ?? 0.0;
    }

    // ── Save ─────────────────────────────────────────────────────────────

    public function save(): void
    {
        $this->successMessage = null;
        $this->errorMessage   = null;
        $this->computeCalcHours();   // ensure values are fresh before reading

        try {
            DB::transaction(function () {
                $report = DailyReport::create([
                    'user_id'        => Auth::id(),
                    'date'           => $this->date,
                    'shift'          => $this->shift,
                    'section'        => $this->shop,
                    'hour'           => $this->calcTotal,
                    'ot'             => $this->otToFloat(),
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

    // ── Reset ────────────────────────────────────────────────────────────

    public function resetForm(): void
    {
        $this->shop             = '';
        $this->shift            = !empty($this->shifts) ? $this->shifts[0]['name'] : '';
        $this->ot               = '—';
        $this->hariPengganti    = false;
        $this->hariPenggantiDay = 'Senin';
        $this->date             = today()->format('Y-m-d');
        $this->updateDayName();
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
