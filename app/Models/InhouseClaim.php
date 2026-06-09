<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class InhouseClaim extends Model
{
    protected $fillable = [
        'report_id',
        'tanggal',
        'model',
        'op_no_st',
        'item',
        'qty',
        'satuan',
        'penyebab',
        'tindakan',
        'faktor',
        'stop_hr',
        'lost_hr',
        'status_klaim',
    ];

    protected $casts = [
        'tanggal' => 'date',
    ];

    public function report(): BelongsTo
    {
        return $this->belongsTo(DailyReport::class, 'report_id');
    }
}
