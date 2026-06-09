<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('daily_reports', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->date('date');
            $table->string('shift')->nullable();      // "Shift 1" / "Shift 2" / "Shift 3"
            $table->string('section')->nullable();    // nama section (text for now)
            $table->string('coordinator')->nullable();
            $table->string('approved_by')->nullable();
            $table->string('checked_by')->nullable();
            $table->string('status')->default('draft'); // draft / submitted / approved
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('daily_reports');
    }
};
