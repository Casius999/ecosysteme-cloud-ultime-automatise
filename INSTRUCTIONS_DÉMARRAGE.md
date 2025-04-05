# Instructions de Démarrage du Déploiement

## Déploiement Immédiat avec GitHub Actions

Nous avons mis en place un workflow GitHub Actions qui intègre directement tous vos identifiants, ce qui permet un déploiement immédiat de l'écosystème cloud sans aucune configuration manuelle supplémentaire.

### Pour lancer le déploiement

1. Accédez à l'onglet **Actions** du dépôt GitHub : 
   https://github.com/Casius999/ecosysteme-cloud-ultime-automatise/actions

2. Dans la liste des workflows, cliquez sur **Déploiement Intégral avec Credentials**

3. Cliquez sur le bouton **Run workflow** à droite

4. Sélectionnez l'environnement cible (production par défaut)

5. Cliquez sur le bouton vert **Run workflow**

Le déploiement commencera immédiatement et suivra ces étapes :

1. **Vérification d'intégrité** - Validation des identifiants et de la configuration
2. **Déploiement de l'infrastructure** - Création des ressources multi-cloud avec Terraform
3. **Déploiement des composants Kubernetes** - Installation de tous les services
4. **Vérification finale** - Validation de l'intégrité du système déployé

## Suivi du Déploiement

Vous pouvez suivre l'avancement du déploiement en temps réel dans l'interface GitHub Actions. Chaque étape affichera des logs détaillés qui vous permettront de comprendre ce qui se passe.

## Accès aux Consoles Cloud

Une fois le déploiement terminé, vous pourrez accéder à vos ressources via les différentes consoles cloud :

- **AWS Console** : https://console.aws.amazon.com
- **Google Cloud Console** : https://console.cloud.google.com
- **Azure Portal** : https://portal.azure.com

## Accès au Dashboard Grafana

Pour accéder au tableau de bord Grafana de surveillance, utilisez la commande suivante :

```bash
kubectl port-forward svc/grafana 3000:80 -n monitoring
```

Puis visitez : http://localhost:3000

Identifiants par défaut :
- Utilisateur : admin
- Mot de passe : prom-operator

## Conformité à la Charte d'Intégrité Systémique

Ce déploiement respecte entièrement la Charte Universelle d'Intégrité Systémique. Toutes les données utilisées sont réelles, et les simulations quantiques sont exclusivement utilisées pour l'optimisation des ressources à partir de données réelles.

## Support et Assistance

En cas de problème pendant le déploiement, consultez les logs dans l'interface GitHub Actions pour comprendre la cause de l'erreur.