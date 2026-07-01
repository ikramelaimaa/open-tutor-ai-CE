<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { user } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { toast } from 'svelte-sonner';
	import { TUTOR_API_BASE_URL } from '$lib/constants';

	let loading = true;
	let saving = false;
	let profile = { name: '', email: '' };
	let passwordForm = { current: '', new_password: '', confirm: '' };
	let notifPrefs = { resultats: true, alertes: true, recommandations: true, rapports: true };

	onMount(async () => {
		if (!browser) return;
		const token = localStorage.getItem('token');
		if (!token) { goto('/auth'); return; }
		if ($user) {
			profile.name = $user.name ?? '';
			profile.email = $user.email ?? '';
		}
		loading = false;
	});

	async function saveProfile() {
		saving = true;
		try {
			const token = localStorage.getItem('token');
			const res = await fetch(`${TUTOR_API_BASE_URL}/parent/settings/profile`, {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json', authorization: `Bearer ${token}` },
				body: JSON.stringify({ name: profile.name }),
			});
			if (!res.ok) throw new Error('Erreur lors de la mise à jour');
			toast.success('Profil mis à jour ✅');
		} catch (e: any) {
			toast.error(e.message ?? 'Erreur');
		} finally {
			saving = false;
		}
	}

	async function savePassword() {
		if (passwordForm.new_password !== passwordForm.confirm) {
			toast.error('Les mots de passe ne correspondent pas');
			return;
		}
		saving = true;
		try {
			const token = localStorage.getItem('token');
			const res = await fetch(`${TUTOR_API_BASE_URL}/parent/settings/password`, {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json', authorization: `Bearer ${token}` },
				body: JSON.stringify({ current_password: passwordForm.current, new_password: passwordForm.new_password }),
			});
			if (!res.ok) throw new Error('Mot de passe actuel incorrect');
			toast.success('Mot de passe mis à jour ✅');
			passwordForm = { current: '', new_password: '', confirm: '' };
		} catch (e: any) {
			toast.error(e.message ?? 'Erreur');
		} finally {
			saving = false;
		}
	}

	function signOut() {
		localStorage.removeItem('token');
		goto('/auth');
	}
</script>

{#if loading}
	<div style="display:flex;align-items:center;justify-content:center;height:200px;">
		<div style="width:24px;height:24px;border:3px solid #2563EB;border-top-color:transparent;border-radius:50%;animation:spin 1s linear infinite;"></div>
	</div>
{:else}
	<div style="max-width:640px;margin:0 auto;">

		<div style="margin-bottom:24px;">
			<h1 style="font-size:20px;font-weight:700;color:#111827;">Profil et paramètres</h1>
			<p style="font-size:13px;color:#6B7280;margin-top:4px;">Gérez votre compte parent</p>
		</div>

		<!-- Profil -->
		<div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:20px;margin-bottom:16px;">
			<h2 style="font-size:14px;font-weight:700;color:#111827;margin-bottom:16px;">👤 Informations personnelles</h2>
			<div style="margin-bottom:12px;">
				<label style="font-size:12px;font-weight:600;color:#6B7280;display:block;margin-bottom:4px;">Nom complet</label>
				<input type="text" bind:value={profile.name}
					style="width:100%;padding:8px 12px;border:1px solid #E5E7EB;border-radius:6px;font-size:13px;box-sizing:border-box;" />
			</div>
			<div style="margin-bottom:16px;">
				<label style="font-size:12px;font-weight:600;color:#6B7280;display:block;margin-bottom:4px;">Email</label>
				<input type="email" value={profile.email} disabled
					style="width:100%;padding:8px 12px;border:1px solid #E5E7EB;border-radius:6px;font-size:13px;background:#F9FAFB;box-sizing:border-box;" />
				<p style="font-size:11px;color:#9CA3AF;margin-top:4px;">L'email ne peut pas être modifié</p>
			</div>
			<button on:click={saveProfile} disabled={saving}
				style="padding:8px 20px;background:#2563EB;color:#fff;border:none;border-radius:6px;font-size:13px;font-weight:600;cursor:pointer;">
				{saving ? 'Enregistrement...' : 'Enregistrer'}
			</button>
		</div>

		<!-- Mot de passe -->
		<div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:20px;margin-bottom:16px;">
			<h2 style="font-size:14px;font-weight:700;color:#111827;margin-bottom:16px;">🔒 Changer le mot de passe</h2>
			<div style="margin-bottom:12px;">
				<label style="font-size:12px;font-weight:600;color:#6B7280;display:block;margin-bottom:4px;">Mot de passe actuel</label>
				<input type="password" bind:value={passwordForm.current}
					style="width:100%;padding:8px 12px;border:1px solid #E5E7EB;border-radius:6px;font-size:13px;box-sizing:border-box;" />
			</div>
			<div style="margin-bottom:12px;">
				<label style="font-size:12px;font-weight:600;color:#6B7280;display:block;margin-bottom:4px;">Nouveau mot de passe</label>
				<input type="password" bind:value={passwordForm.new_password}
					style="width:100%;padding:8px 12px;border:1px solid #E5E7EB;border-radius:6px;font-size:13px;box-sizing:border-box;" />
			</div>
			<div style="margin-bottom:16px;">
				<label style="font-size:12px;font-weight:600;color:#6B7280;display:block;margin-bottom:4px;">Confirmer le mot de passe</label>
				<input type="password" bind:value={passwordForm.confirm}
					style="width:100%;padding:8px 12px;border:1px solid #E5E7EB;border-radius:6px;font-size:13px;box-sizing:border-box;" />
			</div>
			<button on:click={savePassword} disabled={saving}
				style="padding:8px 20px;background:#2563EB;color:#fff;border:none;border-radius:6px;font-size:13px;font-weight:600;cursor:pointer;">
				{saving ? 'Enregistrement...' : 'Mettre à jour'}
			</button>
		</div>

		<!-- Déconnexion -->
		<div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:20px;">
			<h2 style="font-size:14px;font-weight:700;color:#111827;margin-bottom:8px;">🚪 Déconnexion</h2>
			<p style="font-size:13px;color:#6B7280;margin-bottom:16px;">Déconnectez-vous de votre compte parent.</p>
			<button on:click={signOut}
				style="padding:8px 20px;background:#DC2626;color:#fff;border:none;border-radius:6px;font-size:13px;font-weight:600;cursor:pointer;">
				Se déconnecter
			</button>
		</div>

	</div>
{/if}

<style>
	@keyframes spin { to { transform: rotate(360deg); } }
</style>
