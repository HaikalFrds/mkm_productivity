<?php

namespace App\Livewire;

use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;
use Livewire\Component;

class MasterData extends Component
{
    // ── Tab ─────────────────────────────────────────────────────────────────
    public string $tab = 'data_master';  // data_master | user

    // ── Loaded data ──────────────────────────────────────────────────────────
    public array $sections   = [];   // v2.section
    public array $shifts     = [];   // v2.shift
    public array $shopModels = [];   // v2.shop_model for smFilter section
    public array $opNumbers  = [];   // v2.op_number for opFilter section
    public array $groups     = [];   // v2.problem_group
    public array $categories = [];   // v2.problem_category (flat, joined with group)
    public array $users      = [];   // nativephp.users

    // ── Filters (section selector for shop_model / op_number) ────────────────
    public int $smFilter = 0;   // section_id; 0 = not yet initialised
    public int $opFilter = 0;

    // ── Form state (shared across all data_master cards) ─────────────────────
    public bool   $formOpen    = false;
    public string $formMode    = 'add';   // 'add' | 'edit'
    public ?int   $formId      = null;
    public string $formContext = '';      // 'section' | 'shift' | 'shop_model' | 'op_number' | 'category'

    // Section form (name only — no code, matching v2)
    public string $fSecName = '';

    // Shift form
    public string $fShiftName   = '';
    public string $fShiftStart  = '07:00';
    public string $fShiftEnd    = '15:00';
    public string $fShiftHours  = '8';
    public string $fShiftPrep   = '15';    // minutes
    public string $fShiftSholat = '10';    // minutes

    // Shop Model form (MHU stored in mnt/unit for display, /60 before DB save)
    public int    $fSmSection = 0;
    public string $fSmName    = '';
    public string $fSmMhu     = '';   // mnt/unit input
    public string $fSmCycle   = '0';

    // Op Number form
    public int    $fOpSection = 0;
    public string $fOpNo      = '';

    // Category form (name + group only — no code, matching v2)
    public int    $fCatGroup = 0;
    public string $fCatName  = '';

    // ── User form ─────────────────────────────────────────────────────────────
    public bool   $userFormOpen = false;
    public string $userFormMode = 'add';   // 'add' | 'reset_pw'
    public ?int   $userFormId   = null;
    public string $fUserNik     = '';
    public string $fUserName    = '';
    public string $fUserRole    = 'operator';
    public string $fUserPass    = '';
    public string $fUserNewPass = '';

    // ── Delete confirm ───────────────────────────────────────────────────────
    public ?int    $deleteId      = null;
    public ?string $deleteName    = null;
    public string  $deleteContext = '';   // 'master' | 'user'

    // ── Flash ────────────────────────────────────────────────────────────────
    public ?string $success = null;
    public ?string $error   = null;

    // ─────────────────────────────────────────────────────────────────────────

    public function mount(): void
    {
        try {
            $this->loadSections();
            $this->initFilters();
            $this->loadDataMaster();
        } catch (\Throwable $e) {
            $this->error = 'Gagal memuat data: ' . $e->getMessage();
        }
    }

    // ── Tab switching ─────────────────────────────────────────────────────────

    public function switchTab(string $tab): void
    {
        $this->tab        = $tab;
        $this->formOpen   = false;
        $this->formId     = null;
        $this->formContext = '';
        $this->userFormOpen = false;
        $this->deleteId   = null;
        $this->success    = null;
        $this->error      = null;

        try {
            match ($tab) {
                'data_master' => $this->loadDataMaster(),
                'user'        => $this->loadUsers(),
                default       => null,
            };
        } catch (\Throwable $e) {
            $this->error = 'Gagal memuat data: ' . $e->getMessage();
        }
    }

    // ── Data loaders ─────────────────────────────────────────────────────────

    private function loadDataMaster(): void
    {
        $this->loadSections();
        $this->initFilters();
        $this->loadShifts();
        $this->loadShopModels();
        $this->loadOpNumbers();
        $this->loadCategories();
    }

    private function initFilters(): void
    {
        if (!empty($this->sections)) {
            if ($this->smFilter === 0) {
                $this->smFilter = $this->sections[0]['id'];
            }
            if ($this->opFilter === 0) {
                $this->opFilter = $this->sections[0]['id'];
            }
        }
    }

    public function updatedSmFilter(): void
    {
        try { $this->loadShopModels(); } catch (\Throwable) {}
    }

    public function updatedOpFilter(): void
    {
        try { $this->loadOpNumbers(); } catch (\Throwable) {}
    }

    private function loadSections(): void
    {
        $this->sections = DB::connection('v2')
            ->table('section')
            ->orderBy('name')
            ->get(['id', 'name'])
            ->map(fn ($r) => (array) $r)
            ->toArray();
    }

    private function loadShifts(): void
    {
        $this->shifts = DB::connection('v2')
            ->table('shift')
            ->orderBy('id')
            ->get(['id', 'name', 'start_time', 'end_time', 'total_hours', 'preparation_min', 'other_min'])
            ->map(fn ($r) => (array) $r)
            ->toArray();
    }

    private function loadShopModels(): void
    {
        if ($this->smFilter <= 0) {
            $this->shopModels = [];
            return;
        }
        $this->shopModels = DB::connection('v2')
            ->table('shop_model')
            ->join('section', 'section.id', '=', 'shop_model.section_id')
            ->where('shop_model.section_id', $this->smFilter)
            ->select('shop_model.id', 'shop_model.section_id', 'section.name as section_name',
                     'shop_model.model_name', 'shop_model.working_hour', 'shop_model.cycle_time')
            ->orderBy('shop_model.model_name')
            ->get()
            ->map(fn ($r) => (array) $r)
            ->toArray();
    }

    private function loadOpNumbers(): void
    {
        if ($this->opFilter <= 0) {
            $this->opNumbers = [];
            return;
        }
        $this->opNumbers = DB::connection('v2')
            ->table('op_number')
            ->join('section', 'section.id', '=', 'op_number.section_id')
            ->where('op_number.section_id', $this->opFilter)
            ->select('op_number.id', 'op_number.section_id', 'section.name as section_name',
                     'op_number.op_no')
            ->orderBy('op_number.op_no')
            ->get()
            ->map(fn ($r) => (array) $r)
            ->toArray();
    }

    private function loadCategories(): void
    {
        $this->groups = DB::connection('v2')
            ->table('problem_group')
            ->orderBy('order_num')
            ->get(['id', 'name'])
            ->map(fn ($r) => (array) $r)
            ->toArray();

        $this->categories = DB::connection('v2')
            ->table('problem_category')
            ->join('problem_group', 'problem_group.id', '=', 'problem_category.group_id')
            ->select('problem_category.id', 'problem_category.group_id',
                     'problem_group.name as group_name',
                     'problem_category.name',
                     'problem_category.order_num')
            ->orderBy('problem_group.order_num')
            ->orderBy('problem_category.order_num')
            ->get()
            ->map(fn ($r) => (array) $r)
            ->toArray();
    }

    private function loadUsers(): void
    {
        $this->users = DB::connection('nativephp')
            ->table('users')
            ->orderBy('name')
            ->get(['id', 'nik', 'name', 'role'])
            ->map(fn ($r) => (array) $r)
            ->toArray();
    }

    // ── Data Master form helpers ──────────────────────────────────────────────

    public function openAdd(string $context): void
    {
        $this->formOpen    = true;
        $this->formMode    = 'add';
        $this->formId      = null;
        $this->formContext = $context;
        $this->deleteId    = null;
        $this->success     = null;
        $this->error       = null;
        $this->userFormOpen = false;
        $this->resetFormFields($context);
    }

    public function openEdit(int $id, string $context): void
    {
        $this->formOpen    = true;
        $this->formMode    = 'edit';
        $this->formId      = $id;
        $this->formContext = $context;
        $this->deleteId    = null;
        $this->success     = null;
        $this->error       = null;
        $this->userFormOpen = false;
        try {
            $this->populateFormFields($id, $context);
        } catch (\Throwable $e) {
            $this->error = 'Gagal memuat data: ' . $e->getMessage();
        }
    }

    public function closeForm(): void
    {
        $this->formOpen    = false;
        $this->formId      = null;
        $this->formContext = '';
        $this->error       = null;
    }

    private function resetFormFields(string $context): void
    {
        match ($context) {
            'section' => [$this->fSecName] = [''],
            'shift' => [
                $this->fShiftName, $this->fShiftStart, $this->fShiftEnd,
                $this->fShiftHours, $this->fShiftPrep, $this->fShiftSholat,
            ] = ['', '07:00', '15:00', '8', '15', '10'],
            'shop_model' => [
                $this->fSmSection, $this->fSmName, $this->fSmMhu, $this->fSmCycle,
            ] = [$this->smFilter ?: (isset($this->sections[0]) ? $this->sections[0]['id'] : 0), '', '', '0'],
            'op_number' => [
                $this->fOpSection, $this->fOpNo,
            ] = [$this->opFilter ?: (isset($this->sections[0]) ? $this->sections[0]['id'] : 0), ''],
            'category' => [
                $this->fCatGroup, $this->fCatName,
            ] = [isset($this->groups[0]) ? $this->groups[0]['id'] : 0, ''],
            default => null,
        };
    }

    private function populateFormFields(int $id, string $context): void
    {
        match ($context) {
            'section'    => $this->populateSection($id),
            'shift'      => $this->populateShift($id),
            'shop_model' => $this->populateShopModel($id),
            'category'   => $this->populateCategory($id),
            default      => null,
        };
    }

    private function populateSection(int $id): void
    {
        $r = DB::connection('v2')->table('section')->find($id);
        if ($r) { $this->fSecName = $r->name; }
    }

    private function populateShift(int $id): void
    {
        $r = DB::connection('v2')->table('shift')->find($id);
        if ($r) {
            $this->fShiftName   = $r->name;
            $this->fShiftStart  = $r->start_time  ? substr($r->start_time,  0, 5) : '07:00';
            $this->fShiftEnd    = $r->end_time    ? substr($r->end_time,    0, 5) : '15:00';
            $this->fShiftHours  = (string) $r->total_hours;
            $this->fShiftPrep   = (string) ($r->preparation_min ?? 15);
            $this->fShiftSholat = (string) ($r->other_min ?? 10);
        }
    }

    private function populateShopModel(int $id): void
    {
        $r = DB::connection('v2')->table('shop_model')->find($id);
        if ($r) {
            $this->fSmSection = $r->section_id;
            $this->fSmName    = $r->model_name;
            // Display in mnt/unit (v2 converts H/unit × 60)
            $this->fSmMhu     = (string) round((float)$r->working_hour * 60, 2);
            $this->fSmCycle   = (string) $r->cycle_time;
        }
    }

    private function populateCategory(int $id): void
    {
        $r = DB::connection('v2')->table('problem_category')->find($id);
        if ($r) {
            $this->fCatGroup = $r->group_id;
            $this->fCatName  = $r->name;
        }
    }

    // ── Data Master save ──────────────────────────────────────────────────────

    public function save(): void
    {
        $this->error   = null;
        $this->success = null;
        try {
            if ($this->formMode === 'add') {
                $this->doAdd($this->formContext);
            } else {
                $this->doEdit($this->formId, $this->formContext);
            }
            $this->formOpen    = false;
            $this->formId      = null;
            $this->formContext = '';
            $this->reloadContext();
        } catch (\Throwable $e) {
            $this->error = 'Gagal menyimpan: ' . $e->getMessage();
        }
    }

    private function reloadContext(): void
    {
        $this->loadSections();   // always keep sections fresh
        $this->loadShopModels();
        $this->loadOpNumbers();
        match ($this->tab) {
            'data_master' => $this->loadDataMaster(),
            default       => null,
        };
    }

    private function doAdd(string $context): void
    {
        match ($context) {
            'section'    => $this->addSection(),
            'shift'      => $this->addShift(),
            'shop_model' => $this->addShopModel(),
            'op_number'  => $this->addOpNumber(),
            'category'   => $this->addCategory(),
            default => throw new \RuntimeException('Unknown context'),
        };
        $this->success = 'Data berhasil ditambahkan.';
    }

    private function doEdit(int $id, string $context): void
    {
        match ($context) {
            'section'    => $this->editSection($id),
            'shift'      => $this->editShift($id),
            'shop_model' => $this->editShopModel($id),
            'category'   => $this->editCategory($id),
            default => throw new \RuntimeException('Edit tidak didukung.'),
        };
        $this->success = 'Data berhasil diperbarui.';
    }

    private function addSection(): void
    {
        if (empty(trim($this->fSecName))) throw new \RuntimeException('Nama shop wajib diisi.');
        DB::connection('v2')->table('section')->insert(['name' => trim($this->fSecName)]);
    }

    private function editSection(int $id): void
    {
        if (empty(trim($this->fSecName))) throw new \RuntimeException('Nama shop wajib diisi.');
        DB::connection('v2')->table('section')->where('id', $id)->update(['name' => trim($this->fSecName)]);
    }

    private function addShift(): void
    {
        if (empty(trim($this->fShiftName))) throw new \RuntimeException('Nama shift wajib diisi.');
        DB::connection('v2')->table('shift')->insert($this->shiftData());
    }

    private function editShift(int $id): void
    {
        if (empty(trim($this->fShiftName))) throw new \RuntimeException('Nama shift wajib diisi.');
        DB::connection('v2')->table('shift')->where('id', $id)->update($this->shiftData());
    }

    private function shiftData(): array
    {
        return [
            'name'            => trim($this->fShiftName),
            'start_time'      => filled($this->fShiftStart) ? $this->fShiftStart : null,
            'end_time'        => filled($this->fShiftEnd)   ? $this->fShiftEnd   : null,
            'total_hours'     => (float) ($this->fShiftHours  ?: 0),
            'preparation_min' => (float) ($this->fShiftPrep   ?: 15),
            'other_min'       => (float) ($this->fShiftSholat ?: 10),
        ];
    }

    private function addShopModel(): void
    {
        if (!$this->fSmSection) throw new \RuntimeException('Pilih shop terlebih dahulu.');
        if (empty(trim($this->fSmName))) throw new \RuntimeException('Nama model wajib diisi.');
        DB::connection('v2')->table('shop_model')->insert([
            'section_id'   => $this->fSmSection,
            'model_name'   => trim($this->fSmName),
            'working_hour' => (float) ($this->fSmMhu ?: 0) / 60,   // convert mnt→H
            'cycle_time'   => (float) ($this->fSmCycle ?: 0),
        ]);
    }

    private function editShopModel(int $id): void
    {
        if (!$this->fSmSection) throw new \RuntimeException('Pilih shop terlebih dahulu.');
        if (empty(trim($this->fSmName))) throw new \RuntimeException('Nama model wajib diisi.');
        DB::connection('v2')->table('shop_model')->where('id', $id)->update([
            'section_id'   => $this->fSmSection,
            'model_name'   => trim($this->fSmName),
            'working_hour' => (float) ($this->fSmMhu ?: 0) / 60,   // convert mnt→H
            'cycle_time'   => (float) ($this->fSmCycle ?: 0),
        ]);
    }

    private function addOpNumber(): void
    {
        if (!$this->fOpSection) throw new \RuntimeException('Pilih shop terlebih dahulu.');
        if (empty(trim($this->fOpNo))) throw new \RuntimeException('Nomor OP wajib diisi.');
        DB::connection('v2')->table('op_number')->insert([
            'section_id' => $this->fOpSection,
            'op_no'      => trim($this->fOpNo),
        ]);
    }

    private function addCategory(): void
    {
        if (!$this->fCatGroup) throw new \RuntimeException('Pilih group terlebih dahulu.');
        if (empty(trim($this->fCatName))) throw new \RuntimeException('Nama kategori wajib diisi.');
        $max = DB::connection('v2')->table('problem_category')
            ->where('group_id', $this->fCatGroup)->max('order_num') ?? 0;
        DB::connection('v2')->table('problem_category')->insert([
            'group_id'  => $this->fCatGroup,
            'name'      => trim($this->fCatName),
            'order_num' => $max + 1,
        ]);
    }

    private function editCategory(int $id): void
    {
        if (!$this->fCatGroup) throw new \RuntimeException('Pilih group terlebih dahulu.');
        if (empty(trim($this->fCatName))) throw new \RuntimeException('Nama kategori wajib diisi.');
        DB::connection('v2')->table('problem_category')->where('id', $id)->update([
            'group_id' => $this->fCatGroup,
            'name'     => trim($this->fCatName),
        ]);
    }

    // ── Delete (master) ───────────────────────────────────────────────────────

    public function confirmDelete(int $id, string $name, string $context = 'master'): void
    {
        $this->deleteId      = $id;
        $this->deleteName    = $name;
        $this->deleteContext = $context;
        $this->formOpen      = false;
        $this->userFormOpen  = false;
        $this->error         = null;
    }

    public function cancelDelete(): void
    {
        $this->deleteId      = null;
        $this->deleteName    = null;
        $this->deleteContext = '';
    }

    public function doDelete(): void
    {
        $this->error   = null;
        $this->success = null;
        $id            = $this->deleteId;
        $this->deleteId   = null;
        $this->deleteName = null;

        try {
            if ($this->deleteContext === 'user') {
                DB::connection('nativephp')->table('users')->where('id', $id)->delete();
                $this->success = 'User berhasil dihapus.';
                $this->loadUsers();
            } else {
                $this->deleteMasterRecord($id);
            }
        } catch (\Throwable $e) {
            $this->error = 'Gagal menghapus: ' . $e->getMessage();
        }
    }

    private function deleteMasterRecord(int $id): void
    {
        // Context is stored in deleteContext: section|shift|shop_model|op_number|category
        match ($this->deleteContext) {
            'section'    => DB::connection('v2')->table('section')->delete($id),
            'shift'      => DB::connection('v2')->table('shift')->delete($id),
            'shop_model' => DB::connection('v2')->table('shop_model')->delete($id),
            'op_number'  => DB::connection('v2')->table('op_number')->delete($id),
            'category'   => DB::connection('v2')->table('problem_category')->delete($id),
            default      => throw new \RuntimeException('Unknown delete context'),
        };
        $this->success = 'Data berhasil dihapus.';
        $this->deleteContext = '';
        $this->loadDataMaster();
    }

    // ── User CRUD ─────────────────────────────────────────────────────────────

    public function openAddUser(): void
    {
        $this->userFormOpen = true;
        $this->userFormMode = 'add';
        $this->userFormId   = null;
        $this->fUserNik     = '';
        $this->fUserName    = '';
        $this->fUserRole    = 'operator';
        $this->fUserPass    = '';
        $this->fUserNewPass = '';
        $this->formOpen     = false;
        $this->deleteId     = null;
        $this->error        = null;
        $this->success      = null;
    }

    public function openResetPw(int $id): void
    {
        $this->userFormOpen = true;
        $this->userFormMode = 'reset_pw';
        $this->userFormId   = $id;
        $this->fUserNewPass = '';
        $this->formOpen     = false;
        $this->deleteId     = null;
        $this->error        = null;
        $this->success      = null;
    }

    public function closeUserForm(): void
    {
        $this->userFormOpen = false;
        $this->userFormId   = null;
        $this->error        = null;
    }

    public function saveUser(): void
    {
        $this->error   = null;
        $this->success = null;
        try {
            if ($this->userFormMode === 'add') {
                $this->addUser();
            } else {
                $this->resetUserPassword($this->userFormId);
            }
            $this->userFormOpen = false;
            $this->userFormId   = null;
            $this->loadUsers();
        } catch (\Throwable $e) {
            $this->error = 'Gagal: ' . $e->getMessage();
        }
    }

    private function addUser(): void
    {
        if (empty(trim($this->fUserNik)))  throw new \RuntimeException('NIK wajib diisi.');
        if (empty(trim($this->fUserName))) throw new \RuntimeException('Nama wajib diisi.');
        if (empty($this->fUserPass))       throw new \RuntimeException('Password wajib diisi.');

        $exists = DB::connection('nativephp')->table('users')
            ->where('nik', trim($this->fUserNik))->exists();
        if ($exists) throw new \RuntimeException('NIK sudah terdaftar.');

        DB::connection('nativephp')->table('users')->insert([
            'nik'        => trim($this->fUserNik),
            'name'       => trim($this->fUserName),
            'email'      => strtolower(trim($this->fUserNik)) . '@mkm.local',
            'role'       => $this->fUserRole,
            'password'   => Hash::make($this->fUserPass),
            'created_at' => now(),
            'updated_at' => now(),
        ]);
        $this->success = 'User berhasil ditambahkan.';
    }

    private function resetUserPassword(int $id): void
    {
        if (empty($this->fUserNewPass)) throw new \RuntimeException('Password baru wajib diisi.');
        DB::connection('nativephp')->table('users')->where('id', $id)->update([
            'password'   => Hash::make($this->fUserNewPass),
            'updated_at' => now(),
        ]);
        $this->success = 'Password berhasil direset.';
    }

    // ── Render ────────────────────────────────────────────────────────────────

    public function render()
    {
        return view('livewire.master-data')
            ->layout('components.layouts.app', ['title' => 'Master Data']);
    }
}
