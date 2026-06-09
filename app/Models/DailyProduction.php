<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class DailyProduction extends Model
{
    protected $fillable = [
        'report_id',
        'model',
        'plan_unit',
        'actual_unit',
        'plan_whour',
        'actual_whour',
        'ot_2h',
        'ot_3h',
        'ot_11h',
    ];

    protected $casts = [
        'ot_2h'  => 'boolean',
        'ot_3h'  => 'boolean',
        'ot_11h' => 'boolean',
    ];

    public function report(): BelongsTo
    {
        return $this->belongsTo(DailyReport::class, 'report_id');
    }
}
