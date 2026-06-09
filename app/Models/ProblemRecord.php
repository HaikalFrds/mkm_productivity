<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class ProblemRecord extends Model
{
    protected $fillable = [
        'report_id',
        'model',
        'op_st',
        'category',
        'ra_number',
        'description',
        'cause',
        'corrective_action',
        'factor',
        'pic',
        'start_time',
        'end_time',
        'down_time',
        'loss_time',
        'date',
    ];

    protected $casts = [
        'date' => 'date',
    ];

    public function report(): BelongsTo
    {
        return $this->belongsTo(DailyReport::class, 'report_id');
    }
}
